"""Database tables.

Dates are stored as the user's *local* calendar date (``day``) so "today" means the
user's today, not the server's. Timestamps are UTC.
"""

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=utcnow)
    timezone: str = "America/New_York"
    units: str = "imperial"  # imperial (lb) | metric (kg): display only, storage is always kg

    # Body + goal
    sex: str = "male"  # male | female (used for BMR only)
    age: int = 22
    height_cm: float = 175
    weight_kg: float = 75
    goal: str = "lose"  # lose | maintain | gain
    goal_weight_kg: float | None = None
    activity_level: str = "moderate"  # sedentary | light | moderate | active | very_active

    # Coaching style: how hard the coach pushes
    coach_tone: str = "firm"  # gentle | firm | drill

    # Lifestyle context the coach uses
    diet_type: str = "omnivore"  # omnivore | vegetarian | vegan | eggetarian | pescatarian
    allergies: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    cuisines: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    home_foods: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    equipment: str = "full_gym"  # full_gym | home_dumbbells | bodyweight
    training_days_per_week: int = 4
    experience: str = "beginner"  # beginner | intermediate | advanced
    wake_time: str = "07:30"
    sleep_time: str = "23:30"

    # Daily targets (computed, user can override)
    target_kcal: int = 2000
    target_protein_g: int = 150
    target_carbs_g: int = 200
    target_fat_g: int = 65
    target_water_ml: int = 3000
    target_steps: int = 8000

    # Under-13 accounts are created and managed by a parent/guardian
    guardian_name: str | None = None
    guardian_email: str | None = None
    guardian_consent: bool = False

    push_token: str | None = None
    # Free-form facts the coach learns ("skips breakfast", "night shift on Fridays")
    coach_notes: list[str] = Field(default_factory=list, sa_column=Column(JSON))


class Meal(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    day: date = Field(index=True)
    logged_at: datetime = Field(default_factory=utcnow)
    meal_type: str = "snack"  # breakfast | lunch | dinner | snack
    source: str = "text"  # text | photo | manual
    description: str = ""
    items: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    kcal: float = 0
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    fiber_g: float = 0
    coach_feedback: str | None = None


class DailyLog(SQLModel, table=True):
    """Non-food daily metrics: water, steps, weight, check-in."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    day: date = Field(index=True)
    water_ml: int = 0
    steps: int = 0
    weight_kg: float | None = None
    checkin_done: bool = False
    # Calorie target adjustment for this day (negative = recovering from a surplus)
    kcal_adjustment: int = 0


class CoachMessage(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=utcnow)
    role: str  # user | coach
    content: str


class Notification(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=utcnow)
    day: date = Field(index=True)
    kind: str  # morning_brief | meal_missing | protein_pace | water_pace | ...
    title: str
    body: str
    read: bool = False
    pushed: bool = False


class ProgressPhoto(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    day: date = Field(index=True)
    created_at: datetime = Field(default_factory=utcnow)
    pose: str = "front"  # front | side | back
    path: str  # file path on server storage (S3 later)


class WeeklyCheckin(SQLModel, table=True):
    """The weekly 'sit down with your trainer' review."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    week_end: date = Field(index=True)
    created_at: datetime = Field(default_factory=utcnow)
    # Numbers computed by the server
    avg_weight_kg: float | None = None
    prev_avg_weight_kg: float | None = None
    stats: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    # User answers: energy, hunger, sleep, stress (1-5), wins, struggles
    answers: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    photo_ids: list[int] = Field(default_factory=list, sa_column=Column(JSON))
    coach_review: str = ""
    kcal_change: int = 0  # target adjustment the coach applied


class WorkoutPlan(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=utcnow)
    name: str
    # [{"day": "Mon", "focus": "Push", "exercises": [{"slug", "sets", "reps", "rest_s"}]}]
    days: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    notes: str = ""
    active: bool = True


class WorkoutSession(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    day: date = Field(index=True)
    logged_at: datetime = Field(default_factory=utcnow)
    focus: str = ""
    # [{"slug": "bench_press", "sets": [{"reps": 8, "weight_kg": 60, "rpe": 8}]}]
    exercises: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    duration_min: int | None = None
    coach_feedback: str | None = None
