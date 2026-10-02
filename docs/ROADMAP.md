# Roadmap

The north star: everything a human personal trainer does for you, available at any hour, for a fraction of the cost.

## Week 1 (done): MVP loop
- [x] Onboarding: body stats, goal, diet, **home staples**, equipment, schedule, coach intensity
- [x] Target engine (BMR/TDEE, macros, water, steps) with safety floors
- [x] Food logging by text and photo, editable estimates, clarifying questions
- [x] Post-meal coach feedback (protein/carb/fat verdicts + next move)
- [x] Over-budget recovery plan (spread over 2 days, capped, plus steps)
- [x] Proactive nudge engine (11 rules, once per day each, time-windowed, one per tick)
- [x] Coach chat with memory of durable facts ("trains at 6am")
- [x] Meal ideas from home foods that fit the remaining budget; asks first if it doesn't know your food
- [x] Workout plan (full body / upper-lower / PPL by days and equipment), form cues, set logging, rest timer
- [x] Progressive overload suggestions + volume PRs
- [x] Daily weigh-ins, weekly-average trend, weekly check-in with photos and auto target adjustment
- [x] Water + steps (iOS pedometer sync)
- [x] All-ages coaching: kid / teen / adult / senior bands with different targets, nudges, plans and guardrails
- [x] Offline mock mode, 23 backend tests, typed mobile app

## Week 2: from my own first test run
- [ ] Add an Anthropic API key and re-test; offline mode can't size up dishes outside the built-in table
      (e.g. "mutton curry with boneless pieces and kidney") and chat only answers 3 canned questions
- [ ] Grow the offline food table (mutton/goat curry, keema, organ meats, more home dishes) as a fallback
- [ ] "Rebuild plan" gives no feedback and returns the same plan when settings haven't changed;
      show a confirmation and add variety (or rename it to make clear it uses current settings)
- [ ] Use it daily on my phone and log every annoyance here

## Next (weeks 3+)
- [ ] Run it on my own phone for a week with a real API key and fix whatever annoys me
- [ ] Real auth (Supabase Auth or Clerk) instead of `X-User-Id`; Postgres instead of SQLite
- [ ] Deploy backend (Fly.io / Railway) so nudges fire without my laptop on
- [ ] Better food data: USDA FoodData Central + Open Food Facts barcode scan
- [ ] "Plan my day" mode: coach proposes breakfast/lunch/dinner in the morning, evening check-in compares plan vs actual
- [ ] Weekly meal-prep plan + grocery list from home foods
- [ ] Coach memory review screen (see/edit what the coach has learned)
- [ ] Apple Health / Google Health Connect for steps, workouts, weight
- [ ] Kids: real verifiable parental consent (COPPA), parent dashboard, parent-approved reminders,
      kid-friendly visuals (badges, streak pets), bigger tap targets
- [ ] Seniors: large-text mode, simpler navigation, caregiver sharing, chair-based routines
- [ ] Have a pediatric dietitian / physio review the youth and senior rules

## Stretch goals
- [ ] **Voice check-in calls.** The weekly check-in as a real conversation: the coach calls (or you tap "call coach"),
      asks the check-in questions out loud, reacts to answers, and writes the same structured review.
      Build on the existing check-in API: speech-to-text in, coach turn, text-to-speech out
      (realtime voice API or Whisper + TTS). Daily 2-minute "how did today go" calls after that.
- [ ] **Camera form check**: on-device pose estimation (MediaPipe / MoveNet) for squat depth, knee cave,
      bar path, rep counting. Builds on the PosePal hackathon work.
- [ ] Progress photo comparisons (side-by-side, same pose, alignment)
- [ ] Web app (the Expo app already exports to web; needs a desktop layout)
- [ ] Group / buddy accountability
- [ ] Payments and a human-coach escalation tier

## Open questions
- How pushy is too pushy? Need real users to tune nudge frequency per coach tone.
- Photo calorie estimates are the weakest link (hidden oils). Is "photo + one-line note" enough, or do we need portion references?
- Liability: what's the right line between coaching and medical advice for people with conditions?
