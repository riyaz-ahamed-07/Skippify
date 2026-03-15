"""
Attendance update route — mark present or absent.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import get_db
from models import StudentSubject, SubjectOffering, SubjectSlot, MentorAttendance
from schemas import AttendanceUpdateRequest, AttendanceUpdateResponse

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


@router.post("/update", response_model=AttendanceUpdateResponse)
async def update_attendance(req: AttendanceUpdateRequest, db: AsyncSession = Depends(get_db)):
    """
    Mark a class as attended or skipped.
    - 'attend': increments both attended_hours and total_hours
    - 'skip': increments only total_hours
    """
    if req.component == "mentor":
        result = await db.execute(
            select(MentorAttendance).where(MentorAttendance.user_id == req.user_id)
        )
        ma = result.scalar_one_or_none()
        if not ma:
            ma = MentorAttendance(user_id=req.user_id, attended_hours=0, total_hours=0)
            db.add(ma)
        
        if req.action == "increment":
            ma.attended_hours += req.hours
        elif req.action == "decrement":
            ma.attended_hours = max(0, ma.attended_hours - req.hours)
        elif req.action == "attend":
            ma.attended_hours += req.hours
        
        await db.commit()
        return AttendanceUpdateResponse(
            message="Mentor attendance updated",
            new_attended=ma.attended_hours,
            new_total=ma.total_hours # Note: total is still augmented dynamically in dashboard
        )

    # Default Subject Update
    if not req.offering_id:
        raise HTTPException(status_code=400, detail="offering_id required for subject updates")

    result = await db.execute(
        select(StudentSubject)
        .where(
            StudentSubject.user_id == req.user_id,
            StudentSubject.offering_id == req.offering_id,
        )
    )
    ss = result.scalar_one_or_none()
    if not ss:
        raise HTTPException(status_code=404, detail="Student subject enrolment not found")

    if req.action == "attend" or req.action == "increment":
        ss.attended_hours += req.hours
    elif req.action == "decrement":
        ss.attended_hours = max(0, ss.attended_hours - req.hours)
    elif req.action == "skip":
        pass # total_hours is dynamic, so skipping just means not attending
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    await db.commit()

    return AttendanceUpdateResponse(
        message=f"Marked as {'present' if req.action == 'attend' else 'absent'}",
        new_attended=ss.attended_hours,
        new_total=ss.total_hours,
    )
