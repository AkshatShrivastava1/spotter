# Deploying the backend

Free setup: **Neon** (Postgres) + **Render** (API) + **GitHub Actions** (runs nudges every 15 min).

## 1. Database (Neon)
1. Sign up at neon.tech and create a project.
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

## 3. Nudges (GitHub Actions)
Free Render instances sleep when idle, so the in-process scheduler is off in production.
`.github/workflows/nudges.yml` calls `/internal/run-nudges` every 15 minutes instead (and wakes the server).

In the repo: **Settings > Secrets and variables > Actions > New repository secret**:
- `SPOTTER_API_URL`: `https://<your-service>.onrender.com`
- `SPOTTER_CRON_SECRET`: copy the value Render generated for `SPOTTER_CRON_SECRET`

## 4. Point the app at it
In the app: **Settings > Server**, paste the Render URL.

## Known limits (free tier)
- First request after the server sleeps takes ~30-60 s.
- Progress photos are stored in Postgres (max 5 MB each). Fine for a beta; at real scale they should move to
  object storage (S3 / Cloudflare R2) to keep the database small.
