"""
Calendar utilities — expand teaching days, compute future class instances.
"""

from datetime import date, timedelta, datetime
from dataclasses import dataclass


@dataclass
class ClassInstance:
    """A single future class occurrence."""
    date: date
    day_of_week: int  # 0=Mon
    start_time: str
    end_time: str
    duration_hours: int


def expand_teaching_days(
    start_date: date,
    last_working_date: date,
    holidays: set[date],
    exam_periods: list[tuple[date, date]] | None = None,
) -> set[date]:
    """
    Expand all teaching days between start_date and last_working_date,
    excluding weekends (Sat/Sun), holidays, and exam periods.

    Args:
        start_date: First day of the term.
        last_working_date: Last day of teaching.
        holidays: Set of dates that are holidays.
        exam_periods: List of (start, end) tuples for exam-only periods.

    Returns:
        Set of dates that are teaching days.
    """
    if exam_periods is None:
        exam_periods = []

    # Build set of exam-only dates
    exam_dates: set[date] = set()
    for ex_start, ex_end in exam_periods:
        current = ex_start
        while current <= ex_end:
            exam_dates.add(current)
            current += timedelta(days=1)

    teaching_days: set[date] = set()
    current = start_date
    while current <= last_working_date:
        # Skip only Sundays (6) – Saturdays are teaching days unless holiday
        if current.weekday() < 6:
            # Skip holidays
            if current not in holidays:
                # Skip exam-only periods
                if current not in exam_dates:
                    teaching_days.add(current)
        current += timedelta(days=1)

    return teaching_days


def get_future_classes(
    from_date: date,
    last_working_date: date,
    weekly_slots: list[dict],
    teaching_days: set[date],
) -> list[ClassInstance]:
    """
    Generate all future class instances for a subject from from_date
    to last_working_date.

    Args:
        from_date: Start counting from this date (exclusive of today? inclusive).
        last_working_date: Last possible class date.
        weekly_slots: List of dicts with day_of_week, start_time, end_time, duration_hours.
        teaching_days: Set of valid teaching days.

    Returns:
        Sorted list of ClassInstance objects.
    """
    classes: list[ClassInstance] = []

    current = from_date
    while current <= last_working_date:
        if current in teaching_days:
            for slot in weekly_slots:
                if current.weekday() == slot["day_of_week"]:
                    classes.append(ClassInstance(
                        date=current,
                        day_of_week=current.weekday(),
                        start_time=slot["start_time"],
                        end_time=slot["end_time"],
                        duration_hours=slot.get("duration_hours", 1),
                    ))
        current += timedelta(days=1)

    # Sort by date, then start time
    classes.sort(key=lambda c: (c.date, c.start_time))
    return classes


def get_conducted_hours(
    start_time: datetime,
    end_time: datetime,
    weekly_slots: list[dict],
    teaching_days: set[date],
) -> float:
    """
    Calculate total hours conducted for a subject between start_time and end_time.
    Only counts classes that have reached their 'end_time' within a teaching day.
    """
    total_hours = 0.0
    current_date = start_time.date()
    end_date = end_time.date()

    while current_date <= end_date:
        if current_date in teaching_days:
            for slot in weekly_slots:
                if current_date.weekday() == slot["day_of_week"]:
                    # Check if class has ended by 'end_time'
                    class_end_str = slot["end_time"]
                    class_end_time = datetime.strptime(class_end_str, "%H:%M").time()
                    
                    is_past = False
                    if current_date < end_date:
                        is_past = True
                    elif current_date == end_date:
                        if end_time.time() >= class_end_time:
                            is_past = True
                    
                    if is_past:
                        # Also must check if it happened AFTER start_time
                        class_start_str = slot["start_time"]
                        class_start_time = datetime.strptime(class_start_str, "%H:%M").time()
                        
                        is_after_start = False
                        if current_date > start_time.date():
                            is_after_start = True
                        elif current_date == start_time.date():
                            if class_start_time >= start_time.time():
                                is_after_start = True
                        
                        if is_after_start:
                            total_hours += slot.get("duration_hours", 1)
                            
        current_date += timedelta(days=1)
    
    return total_hours
