# Shamy Pipeline — Runbook (Mehul)

## First-time setup
1. `python3.11 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
2. Copy `.env.example` → `.env` and fill the secrets.
3. Google Cloud Console → enable Drive API → create OAuth (Desktop) → download as `credentials.json` in repo root.
4. Run `python -m pipeline.run propose --date 2026-07-07 --platform instagram` once. Browser opens for Drive auth. Save `token.json`.
5. Talk to `@BotFather` on Telegram → `/newbot` → grab the token → save in `.env`.
6. Message your new bot → use `https://api.telegram.org/bot<TOKEN>/getUpdates` → grab the chat ids for Sneha and Mehul.

## Daily flow (v0.1)
1. Listener should be running: `python -m pipeline.approval_listener` (Mehul's laptop or a free worker).
2. Cron schedule (run by hand in v0.1): `python -m pipeline.run propose --date $(date +%Y-%m-%d) --platform instagram`.
3. Sneha taps a variant on her phone → entry lands in `data/approvals.jsonl`.
4. Mehul opens Vizard.ai → drops the asset → pastes the approved caption + hashtags → schedules to IG + X.
5. For TikTok, Mehul DMs Sneha the video + the chosen trending sound link; she taps post in the TikTok app.

## When things break
| Symptom | Action |
|---|---|
| Drive auth expired | Delete `token.json`, rerun any command to re-auth in browser. |
| Gemini quota exhausted | Wait until UTC midnight; alternatively switch to Groq via env flag (v0.2). |
| Listener crashed | Restart it. State is persisted in JSONL, no data loss. |
| Bot doesn't respond | Check token correctness; check internet; check Mehul didn't accidentally `/start` from the wrong account. |
| Privacy flagged a clearly cat-only photo | False positive — re-tag the asset in Drive folder; the AI check is conservative by design. |
| No assets match a pillar | Send Sneha a content prompt (e.g., "we need a snack-reaction shot this week"). |

## Rotation policy
- Secrets rotated every 6 months.
- Drive token re-auth ~weekly (refresh tokens handle most).

## Enabling the cron
1. In GitHub repo settings → Actions → Variables → New repository variable: `PIPELINE_ENABLED = true`.
2. In Secrets → add all the keys (GEMINI, TELEGRAM, DRIVE).
3. After one week of supervised runs in `workflow_dispatch` mode, flip the var to `true` to start the cron.
