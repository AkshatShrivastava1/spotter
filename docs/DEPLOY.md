# Deploying the backend

Free setup: **Neon** (Postgres) + **Render** (API) + **cron-job.org** and **GitHub Actions** (run nudges every 30 min).

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

## 3. Nudges (cron-job.org starts a GitHub workflow)
Free Render instances sleep when idle, so the in-process scheduler is off in production and something
outside has to call `/internal/run-nudges`. Two services split the job:

- **cron-job.org is the clock.** Every 30 minutes from 6:00 to 23:30 New York time it calls GitHub's
  "run workflow" API for `.github/workflows/nudges.yml`.
- **GitHub's runner is the caller.** The workflow curls `/internal/run-nudges` with the cron secret,
  retrying while the server wakes up.

Status: until the cron-job.org job is switched on, the workflow's own 30-minute `schedule:` stays as the
fallback (remove it once cron-job.org is live).

Why both: GitHub's own `schedule:` is best effort (on this quiet repo "every 30 min" ran about every
6 hours), and cron-job.org's requests never wake a sleeping free Render server (instant 503, no spin-up),
while GitHub's runner does. Runs started through the API go right away.

Setup:
1. GitHub repo **Settings > Secrets and variables > Actions**: `SPOTTER_API_URL` (the Render URL) and
   `SPOTTER_CRON_SECRET` (copied from Render).
2. Create a **fine-grained personal access token**: only this repository, permission **Actions: Read and
   write**, nothing else.
3. cron-job.org job:
   - URL `https://api.github.com/repos/<owner>/spotter/actions/workflows/nudges.yml/dispatches`, method POST
   - Headers `Authorization: Bearer <token>`, `Accept: application/vnd.github+json`,
     `X-GitHub-Api-Version: 2022-11-28`, `Content-Type: application/json`
   - Body `{"ref":"main"}`; GitHub answers 204 when the run is queued
   - Schedule `0,30 6-23 * * *`, time zone America/New_York

Server hours: each wake keeps the server up about 15 to 20 minutes, so it's awake roughly 10 hours a day,
well inside the 750 free instance hours a month shared by every free service in the Render workspace.
**Actions > Nudges > Run workflow** runs one pass by hand.

## 4. Point the app at it
In the app: **Settings > Server**, paste the Render URL.

## Known limits (free tier)
- First request after the server sleeps takes ~30-60 s.
- Progress photos are stored in Postgres (max 5 MB each). Fine for a beta; at real scale they should move to
  object storage (S3 / Cloudflare R2) to keep the database small.
