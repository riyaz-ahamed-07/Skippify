"""
Student API routes — config, setup, dashboard, day-view.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import date, datetime

from database import get_db
from models import (
    User, StudentSettings, CalendarTemplate, CalendarEvent,
    SubjectTemplate, SubjectOffering, SubjectSlot,
    StudentSubject, MentorAttendance, ProgramAttendance,
    UserRole,
)
from schemas import (
    StudentSetupRequest, StudentSetupResponse,
    DashboardResponse, SubjectProjection,
    DayViewResponse, ClassInstance,
)
from domain.attendance import compute_subject_projection, compute_overall_attendance
from domain.calendar import expand_teaching_days, get_future_classes, get_conducted_hours

router = APIRouter(prefix="/api", tags=["student"])


@router.get("/config")
async def get_config(
    year: int | None = None,
    semester: int | None = None,
    branch: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get available calendars and subjects for the onboarding flow.
    Returns active calendars + subjects filtered by year/branch/semester.
    """
    # Get active calendars
    cal_result = await db.execute(
        select(CalendarTemplate)
        .options(selectinload(CalendarTemplate.events))
        .where(CalendarTemplate.is_active == True)
    )
    calendars = cal_result.scalars().all()

    # Get subjects
    subj_query = select(SubjectTemplate).options(
        selectinload(SubjectTemplate.offerings).selectinload(SubjectOffering.slots)
    )
    subj_result = await db.execute(subj_query)
    subjects = subj_result.scalars().all()

    return {
        "calendars": [
            {
                "id": c.id,
                "academic_year": c.academic_year,
                "term": c.term,
                "start_date": c.start_date.isoformat(),
                "last_working_date": c.last_working_date.isoformat(),
            }
            for c in calendars
        ],
        "subjects": [
            {
                "id": s.id,
                "code": s.code,
                "name": s.name,
                "credits": s.credits,
                "category": s.category,
                "offerings": [
                    {
                        "id": o.id,
                        "batch": o.batch,
                        "slot": o.slot,
                        "staff": o.staff,
                        "department": o.department,
                        "slots": [
                            {
                                "day_of_week": sl.day_of_week,
                                "start_time": sl.start_time.strftime("%H:%M"),
                                "end_time": sl.end_time.strftime("%H:%M"),
                                "duration_hours": sl.duration_hours,
                            }
                            for sl in o.slots
                        ],
                    }
                    for o in s.offerings
                ],
            }
            for s in subjects
        ],
    }


@router.post("/user/setup", response_model=StudentSetupResponse)
async def setup_user(req: StudentSetupRequest, db: AsyncSession = Depends(get_db)):
    """Save student profile, subjects, and initial attendance data."""

    # Create user
    user = User(name=req.name, role=UserRole.STUDENT.value)
    db.add(user)
    await db.flush()

    # Create settings
    settings = StudentSettings(
        user_id=user.id,
        year=req.year,
        branch=req.branch,
        section=req.section,
        semester=req.semester,
        target_pct=req.target_pct,
        calendar_id=req.calendar_id,
    )
    db.add(settings)

    # Add subjects
    for subj in req.subjects:
        student_subj = StudentSubject(
            user_id=user.id,
            offering_id=subj.offering_id,
            attended_hours=subj.attended_hours,
            total_hours=subj.total_hours,
        )
        db.add(student_subj)

    # Mentor attendance
    if req.mentor_total > 0 or req.mentor_attended > 0:
        mentor = MentorAttendance(
            user_id=user.id,
            attended_hours=req.mentor_attended,
            total_hours=req.mentor_total,
        )
        db.add(mentor)

    # Program attendance
    if req.program_total > 0 or req.program_attended > 0:
        prog = ProgramAttendance(
            user_id=user.id,
            attended_hours=req.program_attended,
            total_hours=req.program_total,
        )
        db.add(prog)

    await db.commit()
    return StudentSetupResponse(user_id=user.id, message="Profile created successfully")


@router.get("/dashboard/{user_id}")
async def get_dashboard(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get per-subject projections and overall attendance for a student."""

    # Load user with all related data
    user_result = await db.execute(
        select(User)
        .options(
            selectinload(User.settings).selectinload(StudentSettings.calendar).selectinload(CalendarTemplate.events),
            selectinload(User.subjects).selectinload(StudentSubject.offering).selectinload(SubjectOffering.slots),
            selectinload(User.subjects).selectinload(StudentSubject.offering).selectinload(SubjectOffering.subject),
            selectinload(User.mentor_attendance),
            selectinload(User.program_attendance),
        )
        .where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.settings:
        raise HTTPException(status_code=400, detail="User has no settings configured")

    settings = user.settings
    calendar = settings.calendar
    if not calendar:
        raise HTTPException(status_code=400, detail="No calendar selected")

    target_pct = settings.target_pct
    now = datetime.now()
    today = now.date()
    setup_time = user.created_at

    # Compute teaching days
    holidays: set[date] = set()
    exam_periods: list[tuple[date, date]] = []
    for ev in calendar.events:
        if ev.event_type == "holiday" or ev.event_type == "event":
            d = ev.start_date
            while d <= ev.end_date:
                holidays.add(d)
                from datetime import timedelta
                d += timedelta(days=1)
        elif ev.event_type == "exam":
            exam_periods.append((ev.start_date, ev.end_date))

    teaching_days = expand_teaching_days(
        calendar.start_date, calendar.last_working_date, holidays, exam_periods
    )

    # Compute per-subject projections
    subject_projections: list[SubjectProjection] = []
    subject_data_for_overall: list[dict] = []

    for ss in user.subjects:
        offering = ss.offering
        subject = offering.subject

        # Get weekly slots for this offering
        weekly_slots = [
            {
                "day_of_week": sl.day_of_week,
                "start_time": sl.start_time.strftime("%H:%M"),
                "end_time": sl.end_time.strftime("%H:%M"),
                "duration_hours": sl.duration_hours,
            }
            for sl in offering.slots
        ]

        # Calculate hours conducted SINCE setup_time
        hours_since_setup = get_conducted_hours(
            start_time=setup_time,
            end_time=now,
            weekly_slots=weekly_slots,
            teaching_days=teaching_days
        )
        current_total_dynamic = ss.total_hours + hours_since_setup

        # Get future classes
        future_classes = get_future_classes(
            from_date=today,
            last_working_date=calendar.last_working_date,
            weekly_slots=weekly_slots,
            teaching_days=teaching_days
        )
        future_class_count = len(future_classes)
        class_duration = offering.slots[0].duration_hours if offering.slots else 1

        # Compute projection
        proj = compute_subject_projection(
            current_attended=ss.attended_hours,
            current_total=current_total_dynamic,
            future_class_count=future_class_count,
            class_duration=class_duration,
            target_pct=target_pct,
        )

        at_risk = proj.can_skip_classes <= 0

        subject_projections.append(SubjectProjection(
            offering_id=offering.id,
            subject_code=subject.code,
            subject_name=subject.name,
            credits=subject.credits,
            current_attended=ss.attended_hours,
            current_total=current_total_dynamic,
            current_pct=proj.current_pct,
            future_classes=future_class_count,
            class_duration=class_duration,
            final_total_hours=proj.final_total_hours,
            projected_pct=proj.projected_pct,
            must_attend=proj.must_attend_classes,
            can_skip=proj.can_skip_classes,
            at_risk=at_risk,
            remaining_hours=proj.remaining_hours,
            required_attended_hours=proj.required_attended_hours,
            extra_hours_needed=proj.extra_hours_needed,
        ))

        # For overall calculation
        subject_data_for_overall.append({
            "attended_hours": ss.attended_hours,
            "total_hours": current_total_dynamic,
        })

    # Get mentor/program hours
    mentor_att = user.mentor_attendance.attended_hours if user.mentor_attendance else 0
    initial_mentor_tot = user.mentor_attendance.total_hours if user.mentor_attendance else 0
    
    # Calculate mentor hours since setup (Wednesday 13:00-15:00)
    mentor_slots = [{"day_of_week": 2, "start_time": "13:00", "end_time": "15:00", "duration_hours": 2}]
    mentor_hours_since_setup = get_conducted_hours(
        start_time=setup_time,
        end_time=now,
        weekly_slots=mentor_slots,
        teaching_days=teaching_days
    )
    mentor_tot = initial_mentor_tot + mentor_hours_since_setup

    prog_att = user.program_attendance.attended_hours if user.program_attendance else 0
    prog_tot = user.program_attendance.total_hours if user.program_attendance else 0

    # Current overall
    current_overall = compute_overall_attendance(
        subject_data_for_overall, mentor_att, mentor_tot, prog_att, prog_tot
    )

    # Projected overall (if student attends only must_attend classes and skips the rest)
    projected_subject_data = []
    for sp in subject_projections:
        proj_attended = sp.current_attended + (sp.must_attend * sp.class_duration)
        projected_subject_data.append({
            "attended_hours": proj_attended,
            "total_hours": sp.final_total_hours,
        })

    projected_overall = compute_overall_attendance(
        projected_subject_data, mentor_att, mentor_tot, prog_att, prog_tot
    )

    return DashboardResponse(
        user_id=user_id,
        target_pct=target_pct,
        subjects=subject_projections,
        current_overall_pct=current_overall,
        projected_overall_pct=projected_overall,
        mentor_attended=mentor_att,
        mentor_total=mentor_tot,
        program_attended=prog_att,
        program_total=prog_tot,
    )


@router.get("/day-view/{user_id}")
async def get_day_view(
    user_id: int,
    view_date: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get today's (or a specific date's) classes with skip-safety info."""

    target_date = date.fromisoformat(view_date) if view_date else date.today()

    # Load user data
    user_result = await db.execute(
        select(User)
        .options(
            selectinload(User.settings).selectinload(StudentSettings.calendar).selectinload(CalendarTemplate.events),
            selectinload(User.subjects).selectinload(StudentSubject.offering).selectinload(SubjectOffering.slots),
            selectinload(User.subjects).selectinload(StudentSubject.offering).selectinload(SubjectOffering.subject),
        )
        .where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.settings or not user.settings.calendar:
        raise HTTPException(status_code=400, detail="User not configured")

    settings = user.settings
    calendar = settings.calendar
    target_pct = settings.target_pct

    # Compute teaching days
    holidays: set[date] = set()
    exam_periods: list[tuple[date, date]] = []
    for ev in calendar.events:
        if ev.event_type in ("holiday", "event"):
            d = ev.start_date
            while d <= ev.end_date:
                holidays.add(d)
                from datetime import timedelta
                d += timedelta(days=1)
        elif ev.event_type == "exam":
            exam_periods.append((ev.start_date, ev.end_date))

    teaching_days = expand_teaching_days(
        calendar.start_date, calendar.last_working_date, holidays, exam_periods
    )

    is_teaching_day = target_date in teaching_days

    classes_today: list[ClassInstance] = []

    if is_teaching_day:
        for ss in user.subjects:
            offering = ss.offering
            subject = offering.subject

            # Check if this subject has a class on target_date's weekday
            for sl in offering.slots:
                if sl.day_of_week == target_date.weekday():
                    # Compute future classes from today onward for projection
                    weekly_slots = [
                        {
                            "day_of_week": s.day_of_week,
                            "start_time": s.start_time.strftime("%H:%M"),
                            "end_time": s.end_time.strftime("%H:%M"),
                            "duration_hours": s.duration_hours,
                        }
                        for s in offering.slots
                    ]
                    future = get_future_classes(target_date, calendar.last_working_date, weekly_slots, teaching_days)
                    future_count = len(future)

                    class_duration = sl.duration_hours
                    proj = compute_subject_projection(
                        ss.attended_hours, ss.total_hours,
                        future_count, class_duration, target_pct,
                    )

                    classes_today.append(ClassInstance(
                        subject_code=subject.code,
                        subject_name=subject.name,
                        offering_id=offering.id,
                        start_time=sl.start_time.strftime("%H:%M"),
                        end_time=sl.end_time.strftime("%H:%M"),
                        duration_hours=sl.duration_hours,
                        can_skip_this=proj.can_skip_classes > 0,
                        remaining_skips=proj.can_skip_classes,
                        must_attend_remaining=proj.must_attend_classes,
                    ))

    # Sort by start time
    classes_today.sort(key=lambda c: c.start_time)

    return DayViewResponse(
        date=target_date,
        is_teaching_day=is_teaching_day,
        classes=classes_today,
    )
