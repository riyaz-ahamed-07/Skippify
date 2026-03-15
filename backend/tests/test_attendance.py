"""
Unit tests for domain attendance and calendar functions.
Run: pytest tests/test_attendance.py -v
"""

import pytest
from datetime import date, timedelta
from domain.attendance import compute_subject_projection, compute_overall_attendance
from domain.calendar import expand_teaching_days, get_future_classes


class TestComputeSubjectProjection:
    """Tests for per-subject attendance projection."""

    def test_basic_projection(self):
        """64/72 attended, 10 future 1-hour classes, 80% target."""
        result = compute_subject_projection(
            current_attended=64,
            current_total=72,
            future_class_count=10,
            class_duration=1,
            target_pct=80.0,
        )
        # final_total = 72 + 10 = 82
        assert result.final_total_hours == 82
        # required_attended = ceil(0.8 * 82) = ceil(65.6) = 66
        assert result.required_attended_hours == 66
        # extra_needed = max(0, 66 - 64) = 2
        assert result.extra_hours_needed == 2
        # must_attend = ceil(2/1) = 2
        assert result.must_attend_classes == 2
        # can_skip = 10 - 2 = 8
        assert result.can_skip_classes == 8
        # current_pct = 64/72 * 100 ≈ 88.89
        assert result.current_pct == 88.89

    def test_already_above_target(self):
        """Student already far above target — all classes can be skipped."""
        result = compute_subject_projection(
            current_attended=90,
            current_total=100,
            future_class_count=5,
            class_duration=1,
            target_pct=80.0,
        )
        # final_total = 100 + 5 = 105
        # required = ceil(0.8 * 105) = ceil(84) = 84
        # extra = max(0, 84 - 90) = 0
        assert result.extra_hours_needed == 0
        assert result.must_attend_classes == 0
        assert result.can_skip_classes == 5

    def test_below_target_impossible(self):
        """Student can't reach target even attending all remaining classes."""
        result = compute_subject_projection(
            current_attended=10,
            current_total=50,
            future_class_count=5,
            class_duration=1,
            target_pct=80.0,
        )
        # final_total = 50 + 5 = 55
        # required = ceil(0.8 * 55) = ceil(44) = 44
        # extra = max(0, 44 - 10) = 34
        # must_attend = ceil(34/1) = 34, but clamped to 5
        assert result.must_attend_classes == 5
        assert result.can_skip_classes == 0

    def test_two_hour_classes(self):
        """Classes that are 2 hours each."""
        result = compute_subject_projection(
            current_attended=64,
            current_total=72,
            future_class_count=5,
            class_duration=2,
            target_pct=80.0,
        )
        # remaining_hours = 5 * 2 = 10
        # final_total = 72 + 10 = 82
        assert result.final_total_hours == 82
        assert result.remaining_hours == 10
        # required = ceil(0.8 * 82) = 66
        # extra = max(0, 66 - 64) = 2
        # must_attend = ceil(2/2) = 1
        assert result.must_attend_classes == 1
        assert result.can_skip_classes == 4

    def test_zero_future_classes(self):
        """No future classes remaining."""
        result = compute_subject_projection(
            current_attended=40,
            current_total=50,
            future_class_count=0,
            class_duration=1,
            target_pct=80.0,
        )
        assert result.must_attend_classes == 0
        assert result.can_skip_classes == 0
        assert result.current_pct == 80.0

    def test_zero_current_total(self):
        """No classes conducted yet."""
        result = compute_subject_projection(
            current_attended=0,
            current_total=0,
            future_class_count=10,
            class_duration=1,
            target_pct=80.0,
        )
        # final_total = 0 + 10 = 10
        # required = ceil(0.8 * 10) = 8
        assert result.must_attend_classes == 8
        assert result.can_skip_classes == 2

    def test_75_percent_target(self):
        """Custom target of 75%."""
        result = compute_subject_projection(
            current_attended=64,
            current_total=72,
            future_class_count=10,
            class_duration=1,
            target_pct=75.0,
        )
        # final_total = 82
        # required = ceil(0.75 * 82) = ceil(61.5) = 62
        # extra = max(0, 62 - 64) = 0
        assert result.extra_hours_needed == 0
        assert result.must_attend_classes == 0
        assert result.can_skip_classes == 10


class TestComputeOverallAttendance:
    """Tests for weighted overall attendance formula."""

    def test_basic_overall(self):
        """Standard case with multiple subjects + mentor hours."""
        subjects = [
            {"attended_hours": 54, "total_hours": 72},  # 75%
            {"attended_hours": 60, "total_hours": 72},  # 83.3%
            {"attended_hours": 38, "total_hours": 45},  # 84.4%
        ]
        result = compute_overall_attendance(
            subjects,
            mentor_attended=8, mentor_total=10,
            program_attended=4, program_total=4,
        )
        # total_attended = 54 + 60 + 38 + 8 + 4 = 164
        # total_conducted = 72 + 72 + 45 + 10 + 4 = 203
        # overall = 164/203 * 100 ≈ 80.79
        assert result == 80.79

    def test_no_mentor_program(self):
        """Without mentor/program hours."""
        subjects = [
            {"attended_hours": 50, "total_hours": 60},
        ]
        result = compute_overall_attendance(subjects)
        assert result == 83.33

    def test_empty_subjects(self):
        """No subjects enrolled."""
        result = compute_overall_attendance([])
        assert result == 100.0

    def test_with_only_mentor(self):
        """Only mentor hours, no subjects."""
        result = compute_overall_attendance(
            [], mentor_attended=8, mentor_total=10,
        )
        assert result == 80.0


class TestExpandTeachingDays:
    """Tests for teaching day expansion."""

    def test_basic_expansion(self):
        """Simple week with no holidays."""
        start = date(2026, 3, 16)  # Monday
        end = date(2026, 3, 20)    # Friday
        result = expand_teaching_days(start, end, holidays=set())
        assert len(result) == 5  # Mon-Fri
        assert date(2026, 3, 16) in result
        assert date(2026, 3, 20) in result

    def test_excludes_weekends(self):
        """Two weeks includes weekends that should be excluded."""
        start = date(2026, 3, 16)  # Monday
        end = date(2026, 3, 27)    # Friday (next week)
        result = expand_teaching_days(start, end, holidays=set())
        assert len(result) == 10  # 2 full weeks, no weekends
        assert date(2026, 3, 21) not in result  # Saturday
        assert date(2026, 3, 22) not in result  # Sunday

    def test_excludes_holidays(self):
        """Holidays should be excluded."""
        start = date(2026, 3, 16)
        end = date(2026, 3, 20)
        holidays = {date(2026, 3, 17), date(2026, 3, 18)}  # Tue, Wed
        result = expand_teaching_days(start, end, holidays)
        assert len(result) == 3  # Mon, Thu, Fri

    def test_excludes_exam_periods(self):
        """Exam periods should be excluded."""
        start = date(2026, 3, 16)
        end = date(2026, 3, 27)
        exam_periods = [(date(2026, 3, 23), date(2026, 3, 27))]
        result = expand_teaching_days(start, end, set(), exam_periods)
        assert len(result) == 5  # Only first week


class TestGetFutureClasses:
    """Tests for future class instance generation."""

    def test_basic_future_classes(self):
        """Generate classes for a subject with Mon/Wed/Fri slots."""
        start = date(2026, 3, 16)  # Monday
        end = date(2026, 3, 27)    # Friday
        teaching_days = expand_teaching_days(start, end, set())

        weekly_slots = [
            {"day_of_week": 0, "start_time": "09:00", "end_time": "10:00", "duration_hours": 1},
            {"day_of_week": 2, "start_time": "09:00", "end_time": "10:00", "duration_hours": 1},
            {"day_of_week": 4, "start_time": "09:00", "end_time": "10:00", "duration_hours": 1},
        ]
        classes = get_future_classes(start, end, weekly_slots, teaching_days)
        assert len(classes) == 6  # 3 per week × 2 weeks

    def test_with_holidays(self):
        """Holiday on a class day should remove that instance."""
        start = date(2026, 3, 16)
        end = date(2026, 3, 20)
        holidays = {date(2026, 3, 18)}  # Wednesday
        teaching_days = expand_teaching_days(start, end, holidays)

        weekly_slots = [
            {"day_of_week": 0, "start_time": "09:00", "end_time": "10:00", "duration_hours": 1},
            {"day_of_week": 2, "start_time": "09:00", "end_time": "10:00", "duration_hours": 1},
        ]
        classes = get_future_classes(start, end, weekly_slots, teaching_days)
        assert len(classes) == 1  # Only Monday, not Wednesday
