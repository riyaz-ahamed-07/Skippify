"""
Core attendance math — deterministic, pure functions.

These functions implement the per-subject and overall attendance formulas
exactly as specified. They have NO side effects and NO database access.
"""

import math
from dataclasses import dataclass


@dataclass
class SubjectProjectionResult:
    """Result of computing attendance projection for one subject."""
    current_pct: float
    final_total_hours: float
    remaining_hours: float
    required_attended_hours: int
    extra_hours_needed: int
    must_attend_classes: int
    can_skip_classes: int
    projected_pct: float  # if student attends only must_attend classes


def compute_subject_projection(
    current_attended: float,
    current_total: float,
    future_class_count: int,
    class_duration: int = 1,
    target_pct: float = 80.0,
) -> SubjectProjectionResult:
    """
    Compute per-subject attendance projection.

    Args:
        current_attended: Hours attended so far.
        current_total: Total hours conducted so far.
        future_class_count: Number of future class instances remaining.
        class_duration: Duration (in hours) of each class (1 or 2).
        target_pct: Target attendance percentage (default 80).

    Returns:
        SubjectProjectionResult with all computed values.
    """
    # Current percentage
    if current_total > 0:
        current_pct = (current_attended / current_total) * 100
    else:
        current_pct = 100.0 if current_attended >= 0 else 0.0

    # Future hours
    remaining_hours = future_class_count * class_duration

    # Final total hours at end of term
    final_total_hours = current_total + remaining_hours

    # Required attended hours to reach target
    required_attended_hours = math.ceil((target_pct / 100) * final_total_hours)

    # Extra hours the student must attend in the future
    extra_hours_needed = max(0, required_attended_hours - current_attended)

    # How many future classes must be attended
    if class_duration > 0:
        must_attend_classes = math.ceil(extra_hours_needed / class_duration)
    else:
        must_attend_classes = 0

    # Clamp: can't attend more classes than exist
    must_attend_classes = min(must_attend_classes, future_class_count)

    # How many future classes can be skipped
    can_skip_classes = max(0, future_class_count - must_attend_classes)

    # Projected percentage if student attends exactly must_attend classes
    projected_attended = current_attended + (must_attend_classes * class_duration)
    if final_total_hours > 0:
        projected_pct = (projected_attended / final_total_hours) * 100
    else:
        projected_pct = 100.0

    return SubjectProjectionResult(
        current_pct=round(current_pct, 2),
        final_total_hours=final_total_hours,
        remaining_hours=remaining_hours,
        required_attended_hours=required_attended_hours,
        extra_hours_needed=extra_hours_needed,
        must_attend_classes=must_attend_classes,
        can_skip_classes=can_skip_classes,
        projected_pct=round(projected_pct, 2),
    )


def compute_overall_attendance(
    subjects: list[dict],
    mentor_attended: float = 0,
    mentor_total: float = 0,
    program_attended: float = 0,
    program_total: float = 0,
) -> float:
    """
    Compute weighted overall attendance.

    Formula:
        Overall % = (sum of attended hours across all components)
                   / (sum of total hours across all components) × 100

    Each subject dict must have:
        - "attended_hours": float
        - "total_hours": float

    Args:
        subjects: List of dicts with attended_hours and total_hours.
        mentor_attended: Mentor meeting attended hours.
        mentor_total: Mentor meeting total hours.
        program_attended: Program/event attended hours.
        program_total: Program/event total hours.

    Returns:
        Overall attendance percentage as float.
    """
    total_attended = sum(s["attended_hours"] for s in subjects)
    total_conducted = sum(s["total_hours"] for s in subjects)

    # Add mentor and program hours
    total_attended += mentor_attended + program_attended
    total_conducted += mentor_total + program_total

    if total_conducted <= 0:
        return 100.0

    return round((total_attended / total_conducted) * 100, 2)
