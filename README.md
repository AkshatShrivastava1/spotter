# Spotter: an AI personal trainer that's actually on you

Most fitness apps are logbooks. You open them, type in your lunch, and they say nothing.
Spotter is built to do what a good personal trainer does: it **notices, follows up, and tells you the next move**.

- Logs food from text ("3 rotis, dal, some bhindi") or a photo, then **reacts like a coach**:
  "Protein was light, 26 g vs ~40 g for lunch. 1,560 kcal and 134 g protein left; make dinner protein-first."
- **Proactive nudges** through the day: weigh-in reminder, morning game plan, "did you eat lunch?",
  protein / water / steps pace checks, workout reminders, end-of-day honesty check, "haven't heard from you".
- **Over budget? Fix forward, not crash diet.** The surplus gets spread over the next 2 days (capped at 10%),
  plus a walk. No skipped meals, no punishment cardio.
- **Meal ideas from what you actually cook.** It asks for your home staples first, then builds plates around
  them that fit your remaining calories and protein.
- **Training plan + form coaching.** Plan built from your equipment and days per week, form cues and common
  mistakes for every lift, set logging with rest timer, and progressive overload ("every set hit 8, next time 140 lb").
- **Weekly check-in, like sitting down with your trainer.** Daily weigh-ins compared as **weekly averages**
  (not day-to-day water noise), front/side progress photos, energy/hunger/sleep/stress questions, then a review
  and an automatic calorie adjustment if you've been consistent and the trend has stalled.
- Coach intensity is a setting: **gentle, firm, or drill sergeant**.
- **For every age, 6 and up.** The coach changes what it's allowed to do by age band:
  - **Kids (6-12)**: set up by a parent/guardian. No calories, diets, weigh-ins or photos, ever. Coaching is about
    active play (60 min/day), water, sleep and colourful plates; workouts are play-based bodyweight games.
  - **Teens (13-17)**: fueling sport and school, protein and plants, technique-first training with moderate loads.
    No deficits, bulks, weight goals, progress photos or "over budget" messaging.
  - **Adults (18-64)**: the full coaching loop above.
  - **Older adults (65+)**: strength + balance plans (sit-to-stand, step-ups, single-leg balance), no heavy barbell
    lifts, higher protein floor, gentler calorie changes, max 4 training days, doctor check-in prompts.

## Repo layout

```
backend/   FastAPI + SQLModel API, coach engine, nudge scheduler, tests
mobile/    Expo (React Native + TypeScript, expo-router) app; also runs on web
docs/      roadmap and design notes
```

## Run it locally

### 1. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # add SPOTTER_ANTHROPIC_API_KEY for real AI; leave blank for offline mode
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000/docs for the interactive API. `pytest` runs the test suite.

**Offline / mock mode.** With no API key, everything still works: food parsing uses a built-in food table
(Indian home food + common US items), and coaching messages come from deterministic templates.
Adding a key upgrades parsing accuracy, enables photo estimates, and gives the coach a real voice.

### 2. Mobile app

```bash
cd mobile
npm install
npx expo start            # press w for web, or scan the QR with Expo Go
```

On a physical phone, the app must reach your laptop: set the server URL during onboarding
(or in Settings) to your laptop's LAN IP, e.g. `http://192.168.1.20:8000`, or start with
`EXPO_PUBLIC_API_URL=http://192.168.1.20:8000 npx expo start`.

Push notifications need a physical device and a development build (`npx expo run:ios` / `run:android`, or EAS).
Expo Go can't receive remote push on Android anymore. Every nudge also lands in the in-app Coach → Nudges inbox,
so you can test the coaching loop without push.

## How the coach thinks

The rule: **numbers are computed, words are generated.**

1. `targets.py`: Mifflin-St Jeor BMR × activity, goal delta, protein by g/kg, safety floors.
2. `coach/context.py`: builds a factual snapshot of the day (eaten, remaining, pace vs time of day, flags).
3. `coach/feedback.py`, `nudges.py`, `checkin.py`, `training.py`: deterministic decisions
   (is protein behind? is this a recovery day? should the target change? add weight next session?).
4. The LLM (`llm.py`) only phrases those decisions in the coach's voice and parses messy food input.
   It's never trusted to invent intake, targets, or weights, and every feature has a non-LLM fallback.

That keeps the advice consistent and testable, and the app keeps working if the model call fails.

## Status

Week 1 MVP. Before launching kid accounts publicly, the guardian step needs to become real COPPA-compliant
verifiable parental consent (and app-store kids-category review). See [docs/ROADMAP.md](docs/ROADMAP.md) for what's next (voice check-in calls, camera form check,
wearable sync, real auth, web app).

Not medical advice. Spotter enforces calorie floors and steers people to a doctor on pain, injury, or
disordered-eating signals, but it isn't a substitute for professional care.
