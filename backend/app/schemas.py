from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class OnboardingIn(BaseModel):
    name: str
    timezone: str = "America/New_York"
    units: Literal["imperial", "metric"] = "imperial"
    sex: Literal["male", "female"] = "male"
    age: int = Field(ge=6, le=110)
    height_cm: float = Field(gt=90, lt=250)
    weight_kg: float = Field(gt=10, lt=350)
    goal: Literal["lose", "maintain", "gain"] = "lose"
    goal_weight_kg: float | None = None
    activity_level: Literal["sedentary", "light", "moderate", "active", "very_active"] = "moderate"
    coach_tone: Literal["gentle", "firm", "drill"] = "firm"
    diet_type: Literal["omnivore", "vegetarian", "vegan", "eggetarian", "pescatarian"] = "omnivore"
    allergies: list[str] = []
    cuisines: list[str] = []
    home_foods: list[str] = []
    equipment: Literal["full_gym", "home_dumbbells", "bodyweight"] = "full_gym"
    training_days_per_week: int = Field(4, ge=1, le=6)
    experience: Literal["beginner", "intermediate", "advanced"] = "beginner"
    wake_time: str = "07:30"
    sleep_time: str = "23:30"
    guardian_name: str | None = None
    guardian_email: str | None = None
    guardian_consent: bool = False

    @model_validator(mode="after")
    def age_rules(self):
        if self.age < 18:
            # Kids and teens never get a weight-loss or bulking target from an app.
            self.goal = "maintain"
            self.goal_weight_kg = None
            self.coach_tone = "gentle" if self.age < 13 else ("firm" if self.coach_tone == "drill" else self.coach_tone)
        if self.age < 13 and not (self.guardian_consent and self.guardian_name):
            raise ValueError("Under 13: a parent or guardian needs to set up the account and give consent.")
        return self


class ProfilePatch(BaseModel):
    name: str | None = None
    units: Literal["imperial", "metric"] | None = None
    timezone: str | None = None
    weight_kg: float | None = None
    goal: Literal["lose", "maintain", "gain"] | None = None
    goal_weight_kg: float | None = None
    activity_level: Literal["sedentary", "light", "moderate", "active", "very_active"] | None = None
    coach_tone: Literal["gentle", "firm", "drill"] | None = None
    diet_type: Literal["omnivore", "vegetarian", "vegan", "eggetarian", "pescatarian"] | None = None
    allergies: list[str] | None = None
    cuisines: list[str] | None = None
    home_foods: list[str] | None = None
    equipment: Literal["full_gym", "home_dumbbells", "bodyweight"] | None = None
    training_days_per_week: int | None = Field(None, ge=1, le=6)
    experience: Literal["beginner", "intermediate", "advanced"] | None = None
    wake_time: str | None = None
    sleep_time: str | None = None
    target_kcal: int | None = None
    target_protein_g: int | None = None
    target_water_ml: int | None = None
    target_steps: int | None = None
    recompute_targets: bool = False


class FoodItem(BaseModel):
    name: str
    quantity: str = ""
    kcal: float
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    fiber_g: float = 0
    confidence: str = "medium"


class ParseIn(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class ParseOut(BaseModel):
    items: list[FoodItem]
    clarifying_question: str = ""
    totals: dict[str, float]


class MealIn(BaseModel):
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"]
    description: str = ""
    items: list[FoodItem]
    source: Literal["text", "photo", "manual"] = "text"


class AmountIn(BaseModel):
    amount: float


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class PushTokenIn(BaseModel):
    token: str


class SetIn(BaseModel):
    reps: int = Field(ge=0, le=200)
    weight_kg: float = 0
    rpe: float | None = None


class ExerciseLogIn(BaseModel):
    slug: str
    sets: list[SetIn]


class WorkoutSessionIn(BaseModel):
    focus: str = ""
    exercises: list[ExerciseLogIn]
    duration_min: int | None = None


class CheckinIn(BaseModel):
    answers: dict[str, Any] = {}
    photo_ids: list[int] = []
