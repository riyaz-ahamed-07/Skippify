"""
SQLAlchemy ORM models for Skippify.
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, Time, DateTime,
    ForeignKey, Text, Enum as SAEnum, func
)
from sqlalchemy.orm import relationship
from database import Base
import enum


# ─── Enums ─────────────────────────────────────────────

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    STUDENT = "student"


class EventType(str, enum.Enum):
    HOLIDAY = "holiday"
    EXAM = "exam"
    EVENT = "event"  # sports day, cultural fest, etc.


# ─── User & Settings ──────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    role = Column(String(20), nullable=False, default=UserRole.STUDENT.value)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    settings = relationship("StudentSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    subjects = relationship("StudentSubject", back_populates="user", cascade="all, delete-orphan")
    mentor_attendance = relationship("MentorAttendance", back_populates="user", uselist=False, cascade="all, delete-orphan")
    program_attendance = relationship("ProgramAttendance", back_populates="user", uselist=False, cascade="all, delete-orphan")


class StudentSettings(Base):
    __tablename__ = "student_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    year = Column(Integer, nullable=True)         # 1, 2, 3, 4
    branch = Column(String(100), nullable=True)   # e.g. "CSE", "AI&DS"
    section = Column(String(10), nullable=True)    # e.g. "A", "B"
    semester = Column(Integer, nullable=True)      # 1-8
    target_pct = Column(Float, nullable=False, default=80.0)
    calendar_id = Column(Integer, ForeignKey("calendar_templates.id"), nullable=True)

    user = relationship("User", back_populates="settings")
    calendar = relationship("CalendarTemplate")


# ─── Calendar ──────────────────────────────────────────

class CalendarTemplate(Base):
    __tablename__ = "calendar_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    academic_year = Column(String(50), nullable=False)   # e.g. "2025-2026"
    term = Column(String(100), nullable=False)            # e.g. "Even Semester – Term 1"
    start_date = Column(Date, nullable=False)
    last_working_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=False)
    raw_text = Column(Text, nullable=True)  # Original extracted PDF text for reference

    events = relationship("CalendarEvent", back_populates="calendar", cascade="all, delete-orphan")


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    calendar_id = Column(Integer, ForeignKey("calendar_templates.id"), nullable=False)
    name = Column(String(300), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    event_type = Column(String(20), nullable=False, default=EventType.HOLIDAY.value)

    calendar = relationship("CalendarTemplate", back_populates="events")


# ─── Subject / Offering / Slot ─────────────────────────

class SubjectTemplate(Base):
    __tablename__ = "subject_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(30), nullable=False)
    name = Column(String(300), nullable=False)
    credits = Column(Integer, nullable=False)
    category = Column(String(100), nullable=True)   # e.g. "Professional Core"
    year = Column(Integer, nullable=True)
    branch = Column(String(100), nullable=True)
    semester = Column(Integer, nullable=True)

    offerings = relationship("SubjectOffering", back_populates="subject", cascade="all, delete-orphan")


class SubjectOffering(Base):
    __tablename__ = "subject_offerings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey("subject_templates.id"), nullable=False)
    batch = Column(String(50), nullable=True)
    slot = Column(String(30), nullable=True)
    department = Column(String(100), nullable=True)
    staff = Column(String(200), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    subject = relationship("SubjectTemplate", back_populates="offerings")
    slots = relationship("SubjectSlot", back_populates="offering", cascade="all, delete-orphan")
    enrolled_students = relationship("StudentSubject", back_populates="offering")


class SubjectSlot(Base):
    __tablename__ = "subject_slots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    offering_id = Column(Integer, ForeignKey("subject_offerings.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    duration_hours = Column(Integer, nullable=False, default=1)

    offering = relationship("SubjectOffering", back_populates="slots")


# ─── Student Subject Enrolment ─────────────────────────

class StudentSubject(Base):
    __tablename__ = "student_subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    offering_id = Column(Integer, ForeignKey("subject_offerings.id"), nullable=False)
    attended_hours = Column(Float, nullable=False, default=0)
    total_hours = Column(Float, nullable=False, default=0)

    user = relationship("User", back_populates="subjects")
    offering = relationship("SubjectOffering", back_populates="enrolled_students")


# ─── Mentor / Program Attendance ───────────────────────

class MentorAttendance(Base):
    __tablename__ = "mentor_attendance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    attended_hours = Column(Float, nullable=False, default=0)
    total_hours = Column(Float, nullable=False, default=0)

    user = relationship("User", back_populates="mentor_attendance")


class ProgramAttendance(Base):
    __tablename__ = "program_attendance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    attended_hours = Column(Float, nullable=False, default=0)
    total_hours = Column(Float, nullable=False, default=0)

    user = relationship("User", back_populates="program_attendance")
