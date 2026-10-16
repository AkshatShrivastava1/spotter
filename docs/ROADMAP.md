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

## Week 2 (done): fixes from my own first test run
- [x] Offline food table grew by 28 dishes (mutton curry, keema, kidney, liver, egg/fish/paneer curries,
      pulao, kadhi, lassi, sweets, plus common US foods)
- [x] Unknown dishes get a low-confidence category guess ("curry", "noodles", "dessert"...) instead of nothing
- [x] Portion words ("small bowl", "large plate") scale estimates; "chicken ... gravy" counts as a curry, not grilled chicken
- [x] Meal ideas stay inside the remaining budget even after a protein top-up; no half eggs
- [x] "Rebuild plan" rotates to different exercises and always says what changed (or why nothing could)
- [x] Offline coach chat answers its own quick prompts (bad day, cravings, meal prep, water, protein)
- [x] 12 new tests (35 total)
- [ ] Add an Anthropic API key and re-test with real AI (needs my key)

## Week 3 (done): ready for the cloud
- [x] Postgres support (works with the `DATABASE_URL` that Render / Railway / Neon / Supabase hand out)
- [x] Same test suite runs against real Postgres in CI, plus a Docker build check
- [x] Dockerfile + Render blueprint; `/health` checks the database
- [x] Nudges can be driven by an external cron (`/internal/run-nudges` + GitHub Actions) so they fire on free hosts that sleep
- [x] Deploy guide in `docs/DEPLOY.md`
- [ ] Create the Neon + Render accounts and do the first deploy (needs my accounts)

## Next (weeks 4+)
- [ ] Run it on my own phone for a week with a real API key and fix whatever annoys me
- [ ] Real auth (Supabase Auth or Clerk) instead of `X-User-Id`
- [ ] Move progress photos to object storage so redeploys don't wipe them
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
