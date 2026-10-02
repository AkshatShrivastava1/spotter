from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..coach.training import create_plan
from ..db import get_session
from ..deps import current_user
from ..models import User
from ..schemas import OnboardingIn, ProfilePatch, PushTokenIn
from ..targets import age_band, compute_targets, is_minor

router = APIRouter(prefix="/users", tags=["users"])


def _apply_targets(user: User) -> dict:
    t = compute_targets(sex=user.sex, age=user.age, height_cm=user.height_cm, weight_kg=user.weight_kg,
                        goal=user.goal, activity_level=user.activity_level)
    user.target_kcal, user.target_protein_g = t.kcal, t.protein_g
    user.target_carbs_g, user.target_fat_g = t.carbs_g, t.fat_g
    user.target_water_ml, user.target_steps = t.water_ml, t.steps
    return {"bmr": t.bmr, "tdee": t.tdee}


@router.post("")
def onboard(body: OnboardingIn, session: Session = Depends(get_session)):
    user = User(**body.model_dump())
    energy = _apply_targets(user)
    session.add(user)
    session.commit()
    session.refresh(user)
    plan = create_plan(session, user)
    session.refresh(user)
    return {"user": user.model_dump(), "energy": energy, "plan_id": plan.id}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return {**user.model_dump(), "age_band": age_band(user.age)}


@router.patch("/me")
def update_me(body: ProfilePatch, user: User = Depends(current_user), session: Session = Depends(get_session)):
    data = body.model_dump(exclude_unset=True)
    recompute = data.pop("recompute_targets", False)
    if is_minor(user.age):
        data.pop("goal", None)
        data.pop("goal_weight_kg", None)
        if data.get("coach_tone") == "drill" or (user.age < 13 and "coach_tone" in data):
            data.pop("coach_tone")
    replan = any(k in data for k in ("equipment", "training_days_per_week", "experience"))
    for k, v in data.items():
        setattr(user, k, v)
    if recompute:
        _apply_targets(user)
    session.add(user)
    session.commit()
    session.refresh(user)
    if replan:
        create_plan(session, user)
    session.refresh(user)
    return {**user.model_dump(), "age_band": age_band(user.age)}


@router.post("/me/push-token")
def push_token(body: PushTokenIn, user: User = Depends(current_user), session: Session = Depends(get_session)):
    user.push_token = body.token
    session.add(user)
    session.commit()
    return {"ok": True}
