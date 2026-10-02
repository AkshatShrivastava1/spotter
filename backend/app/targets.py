"""Daily target math. Deterministic on purpose: the LLM explains numbers, it never invents them."""

from dataclasses import dataclass

ACTIVITY = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

# kcal delta from maintenance per goal
GOAL_DELTA = {"lose": -500, "maintain": 0, "gain": 300}

# protein g per kg bodyweight per goal (higher on a cut to protect muscle)
PROTEIN_PER_KG = {"lose": 2.0, "maintain": 1.6, "gain": 1.8}

KCAL_PER_STEP = 0.04  # rough average for a ~70-80 kg adult


def age_band(age: int) -> str:
    """child 6-12, teen 13-17, adult 18-64, senior 65+. Drives what the coach is allowed to do."""
    if age < 13:
        return "child"
    if age < 18:
        return "teen"
    if age >= 65:
        return "senior"
    return "adult"


def is_minor(age: int) -> bool:
    return age < 18


@dataclass
class Targets:
    kcal: int
    protein_g: int
    carbs_g: int
    fat_g: int
    water_ml: int
    steps: int
    bmr: int
    tdee: int


def bmr_mifflin(sex: str, weight_kg: float, height_cm: float, age: int) -> float:
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if sex == "male" else base - 161


def compute_targets(
    *, sex: str, age: int, height_cm: float, weight_kg: float, goal: str, activity_level: str
) -> Targets:
    band = age_band(age)
    if band in ("child", "teen"):
        return _youth_targets(sex, age, weight_kg, activity_level)

    bmr = bmr_mifflin(sex, weight_kg, height_cm, age)
    tdee = bmr * ACTIVITY.get(activity_level, 1.55)
    kcal = tdee + GOAL_DELTA.get(goal, 0)
    # Never prescribe below a safe floor
    floor = 1500 if sex == "male" else 1200
    kcal = max(kcal, floor)

    protein = PROTEIN_PER_KG.get(goal, 1.8) * weight_kg
    if band == "senior":
        # Older adults need more protein per meal to hold onto muscle; cuts stay gentle.
        protein = 1.3 * weight_kg
        kcal = max(kcal, tdee - 300)
    fat = max(0.8 * weight_kg, kcal * 0.25 / 9)
    carbs = max((kcal - protein * 4 - fat * 9) / 4, 50)

    water = 35 * weight_kg + 500  # baseline + training allowance
    steps = 10000 if goal == "lose" else 8000
    if band == "senior":
        steps = 7000

    return Targets(
        kcal=round(kcal / 10) * 10,
        protein_g=round(protein),
        carbs_g=round(carbs),
        fat_g=round(fat),
        water_ml=int(round(water / 250) * 250),
        steps=steps,
        bmr=round(bmr),
        tdee=round(tdee),
    )


def _youth_targets(sex: str, age: int, weight_kg: float, activity_level: str) -> Targets:
    """Growing bodies: no deficits, no surpluses. Energy is an internal reference only;
    the app never shows kids a calorie budget. Based on rough DRI-style ranges."""
    base = {"child": 1600 if age < 9 else 1900, "teen": 2200 if sex == "female" else 2600}[age_band(age)]
    mult = {"sedentary": 0.9, "light": 0.95, "moderate": 1.0, "active": 1.1, "very_active": 1.2}.get(activity_level, 1.0)
    kcal = base * mult
    protein = max(0.95 * weight_kg, 20)
    fat = kcal * 0.30 / 9
    carbs = (kcal - protein * 4 - fat * 9) / 4
    water = 1500 if age < 9 else (2000 if age < 14 else 2500)
    return Targets(kcal=round(kcal / 10) * 10, protein_g=round(protein), carbs_g=round(carbs), fat_g=round(fat),
                   water_ml=water, steps=12000, bmr=0, tdee=round(kcal))
