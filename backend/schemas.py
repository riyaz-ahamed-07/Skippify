"""
Pydantic schemas for Skippify API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, time


# ─── Admin: Calendar ──────────────────────────────────

class CalendarEventSchema(BaseModel):
    name: str
    start_date: date
    end_date: date
    event_type: str = "holiday"  # holiday | exam | event


class CalendarCreateSchema(BaseModel):
    academic_year: str
    term: str
    start_date: date
    last_working_date: date
    events: list[CalendarEventSchema] = []


class CalendarResponseSchema(BaseModel):
    id: int
    academic_year: str
    term: str
    start_date: date
    last_working_date: date
    is_active: bool
    events: list[CalendarEventSchema] = []

    class Config:
        from_attributes = True


class CalendarEventUpdateSchema(BaseModel):
    id: Optional[int] = None
    name: str
    start_date: date
    end_date: date
    event_type: str = "holiday"


class CalendarUpdateSchema(BaseModel):
    academic_year: Optional[str] = None
    term: Optional[str] = None
    start_date: Optional[date] = None
    last_working_date: Optional[date] = None
    events: Optional[list[CalendarEventUpdateSchema]] = None


# ─── Admin: Subject / Offering ────────────────────────

class SlotSchema(BaseModel):
    day_of_week: int  # 0=Monday
    start_time: str   # "09:00"
    end_time: str     # "10:00"
    duration_hours: int = 1


class OfferingSchema(BaseModel):
    batch: Optional[str] = None
    slot: Optional[str] = None
    department: Optional[str] = None
    staff: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    slots: list[SlotSchema] = []


class SubjectCreateSchema(BaseModel):
    code: str
    name: str
    credits: int
    category: Optional[str] = None
    year: Optional[int] = None
    branch: Optional[str] = None
    semester: Optional[int] = None
    offerings: list[OfferingSchema] = []


class SubjectResponseSchema(BaseModel):
    id: int
    code: str
    name: str
    credits: int
    category: Optional[str] = None
    year: Optional[int] = None
    branch: Optional[str] = None
    semester: Optional[int] = None
    offerings: list[dict] = []

    class Config:
        from_attributes = True


class SubjectUpdateSchema(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    credits: Optional[int] = None
    category: Optional[str] = None
    year: Optional[int] = None
    branch: Optional[str] = None
    semester: Optional[int] = None

class EnrolmentTextRequest(BaseModel):
    text: str
    year: Optional[int] = None
    branch: Optional[str] = None
    semester: Optional[int] = None

# ─── Student: Setup ───────────────────────────────────

class StudentSubjectSetup(BaseModel):
    offering_id: int
    attended_hours: float = 0
    total_hours: float = 0


class StudentSetupRequest(BaseModel):
    name: str
    year: Optional[int] = None
    branch: Optional[str] = None
    section: Optional[str] = None
    semester: Optional[int] = None
    target_pct: float = 80.0
    calendar_id: int
    subjects: list[StudentSubjectSetup] = []
    mentor_attended: float = 0
    mentor_total: float = 0
    program_attended: float = 0
    program_total: float = 0


class StudentSetupResponse(BaseModel):
    user_id: int
    message: str


# ─── Student: Dashboard ──────────────────────────────

class SubjectProjection(BaseModel):
    offering_id: int
    subject_code: str
    subject_name: str
    credits: int
    current_attended: float
    current_total: float
    current_pct: float
    future_classes: int
    class_duration: int
    final_total_hours: float
    projected_pct: float
    must_attend: int
    can_skip: int
    at_risk: bool
    remaining_hours: float
    required_attended_hours: int
    extra_hours_needed: int


class DashboardResponse(BaseModel):
    user_id: int
    target_pct: float
    subjects: list[SubjectProjection]
    current_overall_pct: float
    projected_overall_pct: float
    mentor_attended: float
    mentor_total: float
    program_attended: float
    program_total: float


# ─── Student: Day View ────────────────────────────────

class ClassInstance(BaseModel):
    subject_code: str
    subject_name: str
    offering_id: int
    start_time: str
    end_time: str
    duration_hours: int
    can_skip_this: bool
    remaining_skips: int
    must_attend_remaining: int


class DayViewResponse(BaseModel):
    date: date
    is_teaching_day: bool
    classes: list[ClassInstance]


# ─── Attendance Update ────────────────────────────────

class AttendanceUpdateRequest(BaseModel):
    user_id: int
    offering_id: Optional[int] = None
    component: str = "subject" # "subject" | "mentor"
    action: str  # "attend", "skip", "increment", "decrement"
    hours: float = 1


class AttendanceUpdateResponse(BaseModel):
    message: str
    new_attended: float
    new_total: float
