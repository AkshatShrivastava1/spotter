"""Food text / photo -> itemized macro estimates."""

from __future__ import annotations

import re
from typing import Any

from ..data.foods import FOODS, NUMBER_WORDS
from ..llm import get_llm

ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "quantity": {"type": "string", "description": "e.g. '2 rotis', '1 cup', '150 g'"},
                    "kcal": {"type": "number"},
                    "protein_g": {"type": "number"},
                    "carbs_g": {"type": "number"},
                    "fat_g": {"type": "number"},
                    "fiber_g": {"type": "number"},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                },
                "required": ["name", "quantity", "kcal", "protein_g", "carbs_g", "fat_g", "confidence"],
            },
        },
        "clarifying_question": {
            "type": "string",
            "description": "One short question if a detail would materially change the estimate "
                           "(portion size, oil/ghee, sugar). Empty string if not needed.",
        },
    },
    "required": ["items", "clarifying_question"],
}

PARSE_SYSTEM = """You are a precise nutrition estimator inside a fitness coaching app.
Split the meal into individual items and estimate calories and macros for the portion described.
- Assume typical home-cooked portions when unspecified; for Indian home food assume moderate oil.
- Use realistic, slightly conservative-high estimates (people under-report).
- Never refuse; if unclear, estimate and set confidence low.
Reference values (per serving) you can anchor to:
{refs}"""

PHOTO_SYSTEM = """You are a nutrition estimator looking at a photo of a meal.
Identify each distinct food, estimate portion size from visual cues (plate size, utensils, hands),
and estimate calories and macros. Hidden fats (oil, ghee, butter, dressings) are the biggest source
of error: account for them and mention them in the item name if assumed (e.g. 'dal (with ghee tadka)').
If the image does not show food, return an empty items list and ask what they ate."""


def _find_food(chunk: str) -> tuple[str, Any] | None:
    best: tuple[int, str] | None = None
    for name, (aliases, *_rest) in FOODS.items():
        for term in [name, *aliases]:
            if re.search(rf"\b{re.escape(term)}\b", chunk):
                if best is None or len(term) > best[0]:
                    best = (len(term), name)
    return (best[1], FOODS[best[1]]) if best else None


def _quantity(chunk: str) -> tuple[float, float | None]:
    """Returns (servings multiplier, grams if specified)."""
    g = re.search(r"(\d+(?:\.\d+)?)\s*(g|gm|grams?)\b", chunk)
    if g:
        return 1.0, float(g.group(1))
    n = re.match(r"\s*(\d+(?:\.\d+)?)", chunk)
    if n:
        return float(n.group(1)), None
    first = chunk.strip().split(" ")[0] if chunk.strip() else ""
    return float(NUMBER_WORDS.get(first, 1)), None


def fmt_qty(mult: float, serving: str) -> str:
    """'3', '1 medium' -> '3 medium'; '1.5', '150 g cooked' -> '1.5 x 150 g cooked'."""
    if serving.startswith("1 "):
        return f"{mult:g} {serving[2:]}"
    return serving if mult == 1 else f"{mult:g} x {serving}"


def heuristic_parse(text: str) -> dict[str, Any]:
    parts = [p.strip() for p in re.split(r",|\band\b|\bwith\b|\+|&|\n", text.lower()) if p.strip()]
    items, unknown = [], []
    for chunk in parts:
        found = _find_food(chunk)
        if not found:
            unknown.append(chunk)
            continue
        name, (_aliases, serving, grams, kcal, p, c, f, fib) = found
        mult, g = _quantity(chunk)
        if g:
            mult = g / grams
            qty = f"{g:g} g"
        else:
            qty = fmt_qty(mult, serving)
        items.append({
            "name": name, "quantity": qty,
            "kcal": round(kcal * mult), "protein_g": round(p * mult, 1),
            "carbs_g": round(c * mult, 1), "fat_g": round(f * mult, 1), "fiber_g": round(fib * mult, 1),
            "confidence": "medium",
        })
    question = ""
    if unknown:
        question = f"I couldn't size up: {', '.join(unknown)}. Roughly how much was it, or what's in it?"
    return {"items": items, "clarifying_question": question}


def _refs_for(text: str) -> str:
    lines = []
    for name, (aliases, serving, grams, kcal, p, c, f, _fib) in FOODS.items():
        if any(re.search(rf"\b{re.escape(t)}\b", text.lower()) for t in [name, *aliases]):
            lines.append(f"- {name}, {serving} (~{grams} g): {kcal} kcal, P{p} C{c} F{f}")
    return "\n".join(lines) or "- (no local references matched)"


def parse_text(text: str) -> dict[str, Any]:
    llm = get_llm()
    if llm is None:
        return heuristic_parse(text)
    try:
        return llm.json(
            system=PARSE_SYSTEM.format(refs=_refs_for(text)),
            prompt=f"Meal: {text}",
            schema=ITEM_SCHEMA,
        )
    except Exception:
        return heuristic_parse(text)


def parse_photo(image: bytes, media_type: str, note: str = "") -> dict[str, Any]:
    llm = get_llm()
    if llm is None:
        if note:
            return heuristic_parse(note)
        return {
            "items": [],
            "clarifying_question": "Photo estimates need an AI key on the server. "
                                   "Type what's on the plate and I'll log it.",
        }
    prompt = "Estimate this meal."
    if note:
        prompt += f" The user adds: {note}"
    return llm.json(system=PHOTO_SYSTEM, prompt=prompt, schema=ITEM_SCHEMA, images=[(image, media_type)])


def sum_items(items: list[dict[str, Any]]) -> dict[str, float]:
    return {
        k: round(sum(float(i.get(k, 0) or 0) for i in items), 1)
        for k in ("kcal", "protein_g", "carbs_g", "fat_g", "fiber_g")
    }
