# Deploy

One container (`Dockerfile`): the demo server `python -m web.server` on `$PORT`, health check `GET /healthz`.
The team key is an environment variable (`AI_GATEWAY_API_KEY`), never in git. Every push to `main` runs the
tests in GitHub Actions (`.github/workflows/test.yml`, no key needed: model answers are replayed) and, once the
host is connected, redeploys.

## Live

https://change-check.onrender.com — Render web service `change-check` (free, Docker), created from the public repo URL.
Redeploy after a merge to `main`: call the service's deploy hook (kept outside git, with the team key).

## Render (default)
1. render.com → New + → Blueprint → connect `akirykouski/kakashi_public` → it reads `render.yaml`.
2. Paste the team key into `AI_GATEWAY_API_KEY` when asked. Deploy.
3. From then on: push to `main` → Render rebuilds and redeploys (autoDeploy). URL: `https://change-check.onrender.com` (or the name Render assigns).

## Fly.io (alternative)
`fly launch --copy-config --no-deploy && fly secrets set AI_GATEWAY_API_KEY=… && fly deploy`

## Local
`docker build -t change-check . && docker run -p 8000:8000 --env-file .env change-check`

## Public-demo guard
Free-text remarks call the model on the team key, so the server caps them: 600 characters, 30 per address per
10 minutes, 1000 in total (`REMARK_MAX_CHARS`, `REMARKS_PER_IP_PER_10_MIN`, `REMARKS_TOTAL_CAP`). Demo buttons and
recorded remarks are not counted and need no key. The team key stops working at 19:00.
