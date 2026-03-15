"""
Admin API routes — calendar and enrolment upload + management.
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime

from database import get_db
from models import CalendarTemplate, CalendarEvent, SubjectTemplate, SubjectOffering, SubjectSlot
from schemas import (
    CalendarCreateSchema, CalendarResponseSchema, CalendarUpdateSchema,
    SubjectCreateSchema, SubjectResponseSchema, SubjectUpdateSchema,
    EnrolmentTextRequest,
)
from services.llm import parse_calendar_pdf, parse_enrolment_pdf, parse_enrolment_text

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ─── Calendar Endpoints ──────────────────────────────

@router.post("/calendar/upload")
async def upload_calendar(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    try:
        pdf_bytes = await file.read()
        parsed = parse_calendar_pdf(pdf_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Parsing failed: {str(e)}")

    if "error" in parsed:
        raise HTTPException(status_code=422, detail=parsed)

    # Save to database
    cal = CalendarTemplate(
        academic_year=parsed.get("academic_year", "Unknown"),
        term=parsed.get("term", "Unknown"),
        start_date=datetime.strptime(parsed["start_date"], "%Y-%m-%d").date(),
        last_working_date=datetime.strptime(parsed["last_working_date"], "%Y-%m-%d").date(),
        is_active=False,
        raw_text=None,
    )
    db.add(cal)
    await db.flush()

    for ev in parsed.get("events", []):
        event = CalendarEvent(
            calendar_id=cal.id,
            name=ev["name"],
            start_date=datetime.strptime(ev["start_date"], "%Y-%m-%d").date(),
            end_date=datetime.strptime(ev["end_date"], "%Y-%m-%d").date(),
            event_type=ev.get("event_type", "holiday"),
        )
        db.add(event)

    await db.commit()

    return {"id": cal.id, "parsed": parsed, "message": "Calendar parsed and saved. Review and activate when ready."}


@router.get("/calendars")
async def list_calendars(db: AsyncSession = Depends(get_db)):
    """List all calendars with their events."""
    result = await db.execute(
        select(CalendarTemplate).options(selectinload(CalendarTemplate.events))
    )
    calendars = result.scalars().all()

    return [
        {
            "id": c.id,
            "academic_year": c.academic_year,
            "term": c.term,
            "start_date": c.start_date.isoformat(),
            "last_working_date": c.last_working_date.isoformat(),
            "is_active": c.is_active,
            "events": [
                {
                    "id": e.id,
                    "name": e.name,
                    "start_date": e.start_date.isoformat(),
                    "end_date": e.end_date.isoformat(),
                    "event_type": e.event_type,
                }
                for e in c.events
            ],
        }
        for c in calendars
    ]


@router.put("/calendar/{calendar_id}")
async def update_calendar(calendar_id: int, data: CalendarUpdateSchema, db: AsyncSession = Depends(get_db)):
    """Edit a parsed calendar's data."""
    result = await db.execute(
        select(CalendarTemplate).options(selectinload(CalendarTemplate.events)).where(CalendarTemplate.id == calendar_id)
    )
    cal = result.scalar_one_or_none()
    if not cal:
        raise HTTPException(status_code=404, detail="Calendar not found")

    if data.academic_year is not None:
        cal.academic_year = data.academic_year
    if data.term is not None:
        cal.term = data.term
    if data.start_date is not None:
        cal.start_date = data.start_date
    if data.last_working_date is not None:
        cal.last_working_date = data.last_working_date

    if data.events is not None:
        # Replace all events
        for old_ev in cal.events:
            await db.delete(old_ev)
        await db.flush()

        for ev in data.events:
            new_ev = CalendarEvent(
                calendar_id=cal.id,
                name=ev.name,
                start_date=ev.start_date,
                end_date=ev.end_date,
                event_type=ev.event_type,
            )
            db.add(new_ev)

    await db.commit()
    return {"message": "Calendar updated"}


@router.post("/calendar/{calendar_id}/activate")
async def activate_calendar(calendar_id: int, db: AsyncSession = Depends(get_db)):
    """Activate a calendar for use by students."""
    result = await db.execute(select(CalendarTemplate).where(CalendarTemplate.id == calendar_id))
    cal = result.scalar_one_or_none()
    if not cal:
        raise HTTPException(status_code=404, detail="Calendar not found")

    cal.is_active = True
    await db.commit()
    return {"message": f"Calendar '{cal.term}' is now active"}


@router.delete("/calendar/{calendar_id}")
async def delete_calendar(calendar_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CalendarTemplate).options(selectinload(CalendarTemplate.events)).where(CalendarTemplate.id == calendar_id)
    )
    cal = result.scalar_one_or_none()
    if not cal:
        raise HTTPException(status_code=404, detail="Calendar not found")
    await db.delete(cal)
    await db.commit()
    return {"message": "Calendar deleted"}


# ─── Enrolment / Subject Endpoints ───────────────────

@router.post("/enrolment/upload")
async def upload_enrolment(
    file: UploadFile = File(...),
    year: int | None = None,
    branch: str | None = None,
    semester: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        pdf_bytes = await file.read()
        parsed = parse_enrolment_pdf(pdf_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Parsing failed: {str(e)}")

    if isinstance(parsed, list) and len(parsed) > 0 and "error" in parsed[0]:
        raise HTTPException(status_code=422, detail=parsed[0])

    saved_subjects = []
    for subj_data in parsed:
        subj = SubjectTemplate(
            code=subj_data.get("code", "UNKNOWN"),
            name=subj_data.get("name", "Unknown"),
            credits=subj_data.get("credits", 0),
            category=subj_data.get("category"),
            year=year,
            branch=branch,
            semester=semester,
        )
        db.add(subj)
        await db.flush()

        for off_data in subj_data.get("offerings", []):
            offering = SubjectOffering(
                subject_id=subj.id,
                batch=off_data.get("batch"),
                slot=off_data.get("slot"),
                department=off_data.get("department"),
                staff=off_data.get("staff"),
            )
            db.add(offering)
            await db.flush()

            for slot_data in off_data.get("slots", []):
                from datetime import time as dt_time
                slot = SubjectSlot(
                    offering_id=offering.id,
                    day_of_week=slot_data["day_of_week"],
                    start_time=dt_time.fromisoformat(slot_data["start_time"]),
                    end_time=dt_time.fromisoformat(slot_data["end_time"]),
                    duration_hours=slot_data.get("duration_hours", 1),
                )
                db.add(slot)

        saved_subjects.append({"id": subj.id, "code": subj.code, "name": subj.name})

    await db.commit()
    return {"subjects": saved_subjects, "message": f"Parsed and saved {len(saved_subjects)} subjects."}


@router.post("/enrolment/text")
async def upload_enrolment_text(
    data: EnrolmentTextRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        parsed = parse_enrolment_text(data.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Parsing failed: {str(e)}")

    if isinstance(parsed, list) and len(parsed) > 0 and "error" in parsed[0]:
        raise HTTPException(status_code=422, detail=parsed[0])

    saved_subjects = []
    for subj_data in parsed:
        subj = SubjectTemplate(
            code=subj_data.get("code", "UNKNOWN"),
            name=subj_data.get("name", "Unknown"),
            credits=subj_data.get("credits", 0),
            category=subj_data.get("category"),
            year=data.year,
            branch=data.branch,
            semester=data.semester,
        )
        db.add(subj)
        await db.flush()

        for off_data in subj_data.get("offerings", []):
            offering = SubjectOffering(
                subject_id=subj.id,
                batch=off_data.get("batch"),
                slot=off_data.get("slot"),
                department=off_data.get("department"),
                staff=off_data.get("staff"),
            )
            db.add(offering)
            await db.flush()

            for slot_data in off_data.get("slots", []):
                from datetime import time as dt_time
                slot = SubjectSlot(
                    offering_id=offering.id,
                    day_of_week=slot_data["day_of_week"],
                    start_time=dt_time.fromisoformat(slot_data["start_time"]),
                    end_time=dt_time.fromisoformat(slot_data["end_time"]),
                    duration_hours=slot_data.get("duration_hours", 1),
                )
                db.add(slot)

        saved_subjects.append({"id": subj.id, "code": subj.code, "name": subj.name})

    await db.commit()
    return {"subjects": saved_subjects, "message": f"Parsed and saved {len(saved_subjects)} subjects from text input."}


@router.get("/subjects")
async def list_subjects(
    year: int | None = None,
    branch: str | None = None,
    semester: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List all subjects, optionally filtered by year/branch/semester."""
    query = select(SubjectTemplate).options(
        selectinload(SubjectTemplate.offerings).selectinload(SubjectOffering.slots)
    )
    if year:
        query = query.where(SubjectTemplate.year == year)
    if branch:
        query = query.where(SubjectTemplate.branch == branch)
    if semester:
        query = query.where(SubjectTemplate.semester == semester)

    result = await db.execute(query)
    subjects = result.scalars().all()

    return [
        {
            "id": s.id,
            "code": s.code,
            "name": s.name,
            "credits": s.credits,
            "category": s.category,
            "year": s.year,
            "branch": s.branch,
            "semester": s.semester,
            "offerings": [
                {
                    "id": o.id,
                    "batch": o.batch,
                    "slot": o.slot,
                    "department": o.department,
                    "staff": o.staff,
                    "slots": [
                        {
                            "id": sl.id,
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
    ]


@router.put("/subject/{subject_id}")
async def update_subject(subject_id: int, data: SubjectUpdateSchema, db: AsyncSession = Depends(get_db)):
    """Edit a parsed subject's metadata."""
    result = await db.execute(select(SubjectTemplate).where(SubjectTemplate.id == subject_id))
    subj = result.scalar_one_or_none()
    if not subj:
        raise HTTPException(status_code=404, detail="Subject not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(subj, field, value)

    await db.commit()
    return {"message": "Subject updated"}


@router.delete("/subject/{subject_id}")
async def delete_subject(subject_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SubjectTemplate).options(
            selectinload(SubjectTemplate.offerings).selectinload(SubjectOffering.slots)
        ).where(SubjectTemplate.id == subject_id)
    )
    subj = result.scalar_one_or_none()
    if not subj:
        raise HTTPException(status_code=404, detail="Subject not found")
    await db.delete(subj)
    await db.commit()
    return {"message": "Subject deleted"}
