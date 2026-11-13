# Deploying the backend

Free setup: **Neon** (Postgres) + **Render** (API) + **cron-job.org** (runs nudges every 14 min during the day).

## 1. Database (Neon)
1. Sign up at neon.tech and create a project in **AWS US East 2 (Ohio)**, the same region as the Render service.
2. Copy the connection string (`postgres://...`). Tables are created automatically on first start.

## 2. API (Render)
1. Sign up at render.com with GitHub.
2. **New > Blueprint**, pick this repo. It reads `render.yaml`.
3. When asked, paste:
   - `DATABASE_URL`: the Neon string
   - `SPOTTER_ANTHROPIC_API_KEY`: your key (or leave empty for offline mode)
4. Deploy, then open `https://<your-service>.onrender.com/health`. You should see `"db": "postgresql"`.

The blueprint sets `SPOTTER_ENV=production`. In that mode the server refuses to start if the login secret
is missing or short, the cron secret is missing, or the database isn't Postgres. If a deploy fails, the
Render logs list exactly which setting is wrong.

## 3. Nudges (cron-job.org)
Free Render instances sleep when idle, so the in-process scheduler is off in production and an outside
cron service calls the API instead. (GitHub Actions' `schedule:` was tried first, but on a quiet repo it
ran about every 6 hours instead of every 30 minutes.)

Sign up at cron-job.org (free) and create one job:

- **URL:** `https://<your-service>.onrender.com/internal/run-nudges`
- **Method:** POST, with header `X-Cron-Secret: <SPOTTER_CRON_SECRET from Render>`
- **Schedule:** every 14 minutes from 6:00 to 23:59, time zone America/New_York (cron `*/14 6-23 * * *`)

Why this shape:
- **Every 14 minutes keeps the server awake during the day.** A free Render server sleeps after 15 idle
  minutes and takes up to a minute to wake, but cron-job.org gives up after 30 seconds. Calling every
  14 minutes means only the first call of the morning hits a sleeping server; every other call is fast.
- **It sleeps overnight.** Every reminder window falls between waking up and bedtime, so there's nothing
  to send at night. Awake about 18 hours a day is roughly 550 of the 750 free instance hours a month that
  every free service in the Render workspace shares.
- **No run of failures.** cron-job.org disables a job after 25 failures in a row. With this schedule at
  most one call a day can time out (the 6:00 wake-up), and the next success resets the count.

Backup: **Actions > Nudges > Run workflow** on GitHub runs one pass by hand (needs repo secrets
`SPOTTER_API_URL` and `SPOTTER_CRON_SECRET`).

## 4. Point the app at it
In the app: **Settings > Server**, paste the Render URL.

## Known limits (free tier)
- First request after the server sleeps takes ~30-60 s.
- Progress photos are stored in Postgres (max 5 MB each). Fine for a beta; at real scale they should move to
  object storage (S3 / Cloudflare R2) to keep the database small.
