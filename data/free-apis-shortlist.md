# Free APIs Shortlist for the Shamy Pipeline

> Curated from [`public-apis/public-apis`](https://github.com/public-apis/public-apis).
> Only APIs that are (a) free or have generous free tiers, (b) directly useful to this pipeline, (c) won't require corporate-level approval.

---

## 1. Already chosen (core stack)

| Need | API | Auth | Status |
|---|---|---|---|
| Caption + vision LLM | [Google Gemini API](https://ai.google.dev/) | API key | ✅ chosen |
| Telegram approval bot | [Telegram Bot API](https://core.telegram.org/bots/api) | Bot token | ✅ chosen |
| File storage | [Google Drive API](https://developers.google.com/drive) | OAuth | ✅ chosen |
| Multi-platform publishing | Vizard.ai (private, paid) | Account | ✅ chosen (user has premium) |

## 2. Backup / overflow LLMs (rotate if Gemini quota burns)

| API | Free tier | Notes |
|---|---|---|
| [Groq](https://console.groq.com/) | Generous free Llama inference | Text-only, fast. Use as caption-only fallback. |
| [Together.ai](https://www.together.ai/) | Free Llama + open models | Text-only. |
| [HuggingFace Inference](https://huggingface.co/inference-api) | Free serverless tier | Many vision + text models. Useful as third fallback. |
| [Cloudflare Workers AI](https://developers.cloudflare.com/workers-ai/) | 10k neurons/day free | Llama 3, Llava (vision). Pairs naturally with Cloudflare Workers if we add edge. |

## 3. AI image → video (animation) — rotate to stretch free credits

| API | Free tier | Notes |
|---|---|---|
| [Kling AI](https://klingai.com/) | ~daily free credits via web | Best motion quality for the price. Use for hero posts. |
| [Pixverse](https://pixverse.ai/) | Daily free credits | Solid for cute pet motion. |
| [MiniMax Hailuo](https://hailuoai.video/) | Free trial credits | Strong character motion. |
| [Luma Dream Machine](https://lumalabs.ai/dream-machine) | Daily free generations | Cinematic feel. |
| [Pollinations](https://pollinations.ai/) | Free, no key | OK quality, useful for fallback. |

## 4. Image editing / memes / overlays

| API | Free tier | Notes |
|---|---|---|
| [Gemini 2.5 Flash Image (nano-banana)](https://ai.google.dev/gemini-api/docs/image-generation) | Same Gemini free tier | Meme edits + text overlays + scene tweaks |
| [Cloudinary](https://cloudinary.com/) | 25 credits / mo free | Automatic image manipulation, format conversion, smart cropping |
| [Pollinations Image](https://image.pollinations.ai/) | Free, no key | Fallback for image generation |
| [remove.bg](https://www.remove.bg/api) | 50 free images / mo | Background removal for sticker-style content |

## 5. Music / royalty-free sounds (for IG Reels, slideshow videos)

> Note: TikTok native posts use TikTok's in-app trending sounds — these libraries are for IG Reels backgrounds and for Vizard auto-clipped videos.

| API | Free tier | License |
|---|---|---|
| [Pixabay Music](https://pixabay.com/api/docs/) | Free with API key | Pixabay license — free for commercial, no attribution required |
| [Free Music Archive](https://freemusicarchive.org/api) | Free, no key | Mixed CC licenses — filter by license |
| [Jamendo](https://developer.jamendo.com/v3.0) | Free with API key | CC-licensed music |
| [ccMixter](http://ccmixter.org/) | Free | Creative Commons |

## 6. Filler content / cross-promotion (use sparingly)

| API | Purpose |
|---|---|
| [Cat Facts](https://catfact.ninja/) | Random cat fact, free, no key — good for Story filler ("Did you know..." templates) |
| [MeowFacts](https://github.com/wh-iterabb-it/meowfacts) | Same, alternative |
| [Cataas (Cat-as-a-Service)](https://cataas.com/) | Random cat photos — never use as our content, but useful for testing pipeline without consuming real assets |

## 7. Trend / hashtag research (semi-manual)

There is no fully free Instagram or TikTok hashtag API; what's available is scraped data.

| Tool | Free tier | Notes |
|---|---|---|
| [RapidTags](https://rapidtags.io/) | Free with limits | YouTube-focused; tags hint at search trends |
| [Display Purposes](https://displaypurposes.com/) | Free | IG hashtag suggestions; built-in to many schedulers anyway |
| Manual creator-watching | Free | Maintain `data/trending-sounds.yaml` by watching 5 pet-niche TikTok creators weekly |

## 8. Useful "platformy" utilities

| API | Purpose | Tier |
|---|---|---|
| [GitHub API](https://docs.github.com/rest) | Programmatic commits to `content-log.jsonl` | Free |
| [TimeZoneDB](https://timezonedb.com/) | Timezone math for CET scheduling (built into Python `zoneinfo` so probably skipped) | Free |
| [URL shortener: tinyurl API](https://tinyurl.com/app/dev) | Compact TikTok sound links for Telegram cards | Free tier |

## 9. Explicitly NOT useful (despite being tempting)

- **OpenAI API** — not free, would blow budget.
- **Anthropic Claude API** — not free, would blow budget.
- **Most "trend prediction" APIs** — paid, gimmicky, not worth it.
- **Random pet image APIs (Cataas, Dog API)** — fun for testing, but never as real Shamy content. The brand is *Amy and Sheldon specifically.*
- **OpenAI Sora / Runway Gen-3** — out of budget.

## 10. Decision matrix (when to reach for what)

```
Need:                       Reach for:
─────────────────────────  ─────────────────────────────────────────
Caption for any post        Gemini Vision (sees the photo)
Privacy check               Gemini Vision (same call, different prompt)
Meme overlay                Gemini 2.5 Flash Image
Cat moves in a still        Kling → Pixverse → Hailuo → Luma (rotate)
Photo carousel video        ffmpeg + Ken Burns (no API needed)
Background music for Reel   Pixabay Music API
Story "Did you know" filler Cat Facts API
Trending TikTok sound       Curated trending-sounds.yaml (manual weekly)
Caption fallback if Gemini  Groq Llama 3 (text-only)
```
