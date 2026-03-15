"""
Seed script — insert demo data for testing.
Run: python seed.py
"""

import asyncio
from datetime import date, time
from database import engine, async_session, Base
from models import (
    User, StudentSettings, CalendarTemplate, CalendarEvent,
    SubjectTemplate, SubjectOffering, SubjectSlot,
    StudentSubject, MentorAttendance, ProgramAttendance,
    UserRole,
)


async def seed():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # ─── Admin User ───────────────────────────────
        admin = User(name="Admin", role=UserRole.ADMIN.value)
        db.add(admin)

        # ─── Calendar: Even Semester 2025-2026 ────────
        cal = CalendarTemplate(
            academic_year="2025-2026",
            term="Even Semester – UG",
            start_date=date(2026, 1, 13),
            last_working_date=date(2026, 5, 8),
            is_active=True,
        )
        db.add(cal)
        await db.flush()

        # Holidays and events
        events_data = [
            ("Pongal Holidays", date(2026, 1, 14), date(2026, 1, 16), "holiday"),
            ("Republic Day", date(2026, 1, 26), date(2026, 1, 26), "holiday"),
            ("CIA-1 Exams", date(2026, 2, 16), date(2026, 2, 21), "exam"),
            ("Sports Day", date(2026, 2, 28), date(2026, 2, 28), "event"),
            ("Holi", date(2026, 3, 17), date(2026, 3, 17), "holiday"),
            ("CIA-2 Exams", date(2026, 3, 23), date(2026, 3, 28), "exam"),
            ("Good Friday", date(2026, 4, 3), date(2026, 4, 3), "holiday"),
            ("Puthandu / Tamil New Year", date(2026, 4, 14), date(2026, 4, 14), "holiday"),
            ("Cultural Fest", date(2026, 4, 17), date(2026, 4, 18), "event"),
            ("Labour Day", date(2026, 5, 1), date(2026, 5, 1), "holiday"),
        ]
        for name, start, end, etype in events_data:
            db.add(CalendarEvent(
                calendar_id=cal.id, name=name,
                start_date=start, end_date=end, event_type=etype,
            ))

        # ─── Subjects ─────────────────────────────────
        subjects_data = [
            {
                "code": "19AI307", "name": "Machine Learning", "credits": 4,
                "category": "Professional Core",
                "offerings": [
                    {
                        "batch": "2023-AI-A", "slot": "A1", "staff": "Dr. S. Kumar",
                        "department": "AI&DS",
                        "slots": [
                            (0, time(9, 0), time(10, 0), 1),   # Monday 9-10
                            (2, time(9, 0), time(10, 0), 1),   # Wednesday 9-10
                            (4, time(9, 0), time(10, 0), 1),   # Friday 9-10
                            (3, time(14, 0), time(16, 0), 2),  # Thursday 2-4 (lab)
                        ],
                    },
                ],
            },
            {
                "code": "19AI409", "name": "Deep Learning", "credits": 4,
                "category": "Professional Core",
                "offerings": [
                    {
                        "batch": "2023-AI-A", "slot": "B1", "staff": "Dr. R. Patel",
                        "department": "AI&DS",
                        "slots": [
                            (1, time(10, 0), time(11, 0), 1),  # Tuesday 10-11
                            (3, time(10, 0), time(11, 0), 1),  # Thursday 10-11
                            (4, time(10, 0), time(11, 0), 1),  # Friday 10-11
                            (0, time(14, 0), time(16, 0), 2),  # Monday 2-4 (lab)
                        ],
                    },
                ],
            },
            {
                "code": "19AI413", "name": "Natural Language Processing", "credits": 3,
                "category": "Professional Elective",
                "offerings": [
                    {
                        "batch": "2023-AI-A", "slot": "C1", "staff": "Prof. A. Singh",
                        "department": "AI&DS",
                        "slots": [
                            (0, time(11, 0), time(12, 0), 1),  # Monday 11-12
                            (2, time(11, 0), time(12, 0), 1),  # Wednesday 11-12
                            (4, time(11, 0), time(12, 0), 1),  # Friday 11-12
                        ],
                    },
                ],
            },
            {
                "code": "19AI541", "name": "Computer Vision", "credits": 3,
                "category": "Professional Elective",
                "offerings": [
                    {
                        "batch": "2023-AI-A", "slot": "D1", "staff": "Dr. M. Gupta",
                        "department": "AI&DS",
                        "slots": [
                            (1, time(11, 0), time(12, 0), 1),  # Tuesday 11-12
                            (3, time(11, 0), time(12, 0), 1),  # Thursday 11-12
                            (4, time(14, 0), time(15, 0), 1),  # Friday 2-3
                        ],
                    },
                ],
            },
            {
                "code": "19HS401", "name": "Professional Ethics", "credits": 2,
                "category": "Humanities",
                "offerings": [
                    {
                        "batch": "2023-AI-A", "slot": "E1", "staff": "Prof. L. Sharma",
                        "department": "Humanities",
                        "slots": [
                            (1, time(9, 0), time(10, 0), 1),   # Tuesday 9-10
                            (3, time(9, 0), time(10, 0), 1),   # Thursday 9-10
                        ],
                    },
                ],
            },
        ]

        offering_ids = []
        for s in subjects_data:
            subj = SubjectTemplate(
                code=s["code"], name=s["name"], credits=s["credits"],
                category=s["category"], year=3, branch="AI&DS", semester=6,
            )
            db.add(subj)
            await db.flush()

            for off in s["offerings"]:
                offering = SubjectOffering(
                    subject_id=subj.id, batch=off["batch"], slot=off["slot"],
                    staff=off["staff"], department=off["department"],
                )
                db.add(offering)
                await db.flush()
                offering_ids.append(offering.id)

                for day, st, et, dur in off["slots"]:
                    db.add(SubjectSlot(
                        offering_id=offering.id, day_of_week=day,
                        start_time=st, end_time=et, duration_hours=dur,
                    ))

        # ─── Demo Student ─────────────────────────────
        student = User(name="Demo Student", role=UserRole.STUDENT.value)
        db.add(student)
        await db.flush()

        settings = StudentSettings(
            user_id=student.id, year=3, branch="AI&DS", section="A",
            semester=6, target_pct=80.0, calendar_id=cal.id,
        )
        db.add(settings)

        # Subject attendance (simulating ~75-90% attendance so far)
        attendance_data = [
            (offering_ids[0], 54, 72),   # ML: 54/72 = 75%
            (offering_ids[1], 60, 72),   # DL: 60/72 = 83.3%
            (offering_ids[2], 38, 45),   # NLP: 38/45 = 84.4%
            (offering_ids[3], 33, 42),   # CV: 33/42 = 78.6%
            (offering_ids[4], 20, 26),   # Ethics: 20/26 = 76.9%
        ]
        for oid, attended, total in attendance_data:
            db.add(StudentSubject(
                user_id=student.id, offering_id=oid,
                attended_hours=attended, total_hours=total,
            ))

        # Mentor meeting
        db.add(MentorAttendance(
            user_id=student.id, attended_hours=8, total_hours=10,
        ))

        # Program attendance
        db.add(ProgramAttendance(
            user_id=student.id, attended_hours=4, total_hours=4,
        ))

        await db.commit()
        print("✅ Seed data inserted successfully!")
        print(f"   Admin user ID: {admin.id}")
        print(f"   Student user ID: {student.id}")
        print(f"   Calendar ID: {cal.id}")
        print(f"   Subjects: {len(subjects_data)}")


if __name__ == "__main__":
    asyncio.run(seed())
