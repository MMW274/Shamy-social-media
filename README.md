# Shamy — Social Media Pipeline

A KISS, low-cost, semi-automated pipeline that posts photos and videos of two rescue cats — **Amy** & **Sheldon** (brand: **Shamy**) — to Instagram, X, and TikTok.

- **Instagram:** [@lifewithshamy](https://instagram.com/lifewithshamy)
- **X:** [@LifeWithShamy](https://x.com/LifeWithShamy)
- **TikTok:** TBD

## How it works (high level)

1. Sneha drops phone photos/videos into Google Drive folders.
2. A daily **GitHub Actions cron** picks the next slot from the content calendar, runs a privacy check (Gemini Vision — no humans posted), generates a caption + hashtags + suggested trending sound, and stages the asset.
3. A **Telegram bot** sends the proposal to Sneha & Mehul for one-tap approval.
4. On approve, **Vizard.ai** publishes to Instagram + X. For TikTok, the bot hands the ready video + trending sound to Sneha's phone for a manual tap (preserves TikTok's native sound access).

## Repo contents

- [`docs/superpowers/specs/2026-06-29-shamy-social-pipeline-design.md`](docs/superpowers/specs/2026-06-29-shamy-social-pipeline-design.md) — full design spec
- `data/` — content calendar, post log, pillar definitions, prompt bank
- `pipeline/` — Python modules that run inside GitHub Actions
- `.github/workflows/` — cron schedules and audit jobs

## Status

🚧 Design phase — implementation plan next.
