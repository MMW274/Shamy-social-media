# Shamy Social Media Pipeline — Design Spec

**Date:** 2026-06-29
**Status:** Draft for review
**Owner:** Mehul (uncle / engineer) — supervising on behalf of Sneha & Anish (cat parents)

---

## 1. Purpose

A KISS, low-cost, supervised-then-automated pipeline that posts cute/fun content of two rescue cats — **Amy & Sheldon** (brand: **Shamy**) — to **Instagram**, **X**, and **TikTok**.

The pipeline turns a folder of photos and videos into approved, captioned, hashtagged, optionally-animated social posts with minimal daily effort from Sneha. Mehul supervises during ramp-up, then the system runs hands-off.

## 2. The cast

### The cats

| | Amy | Sheldon |
|---|---|---|
| Look | Fluffy long-hair Maine-Coon-style, brown tabby | Spotted Bengal-style, "cheetah" markings |
| Background | Rescue, gentler upbringing than Sheldon | Rescue with rough early handling, now thriving |
| Age | ~unknown (TBD by Sneha) | ~3.6 years |
| Personality | Active, affectionate, easily startled, sociable with guests, gets moody/zoomy once a month | Cautious, observant, methodical, avoids new visitors, picks his moments — a careful little gentleman |
| Content gold | Confidence arc, big-fluff aesthetic, "drama queen" moments | Trust journey, dignified judgment face, hiding spots |

### The humans (background, never in posts)
- **Sneha** — Mehul's sister, primary caretaker and photographer.
- **Anish** — Sneha's husband, co-caretaker.
- **Location** — Calw district, near Stuttgart, Germany (CET timezone, schedule posts accordingly).

**Privacy rule:** Sneha & Anish appear in some source photos/videos. They must **never** appear in posted content. Enforced by folder boundary + AI vision double-check (see §7).

## 3. Brand

- **Name / handle:** "Shamy" (Sheldon + Amy, BBT-inspired)
- **X:** [@LifeWithShamy](https://x.com/LifeWithShamy) — already created
- **Instagram:** [@lifewithshamy](https://instagram.com/lifewithshamy) — already created
- **TikTok:** `@lifewithshamy` if available, else TBD
- **Bio one-liner:** *"The feline scientists of the household. Sibling rescues thriving in a small German town."*
- **Voice:** Mixed — primarily cat-POV first-person, occasional human-narrator for series like *"Sheldon Reviews ___"*
- **Language:** English only
- **Visual identity:** Warm, soft, natural-light forward. Minimal overlays. Emoji set: 🐾 🍓 🪴 🌿 ☁️ 🎀 🥖. Signature hashtag set: `#LifeWithShamy #AmyAndSheldon #Shamy`.

## 4. Content pillars (6)

Rotate weekly so every pillar appears regularly:

1. **Sibling chaos** — Amy vs Sheldon interactions, sparring, sharing.
2. **Snack reactions** — Treat / fruit / strawberry moments (kitten apple photo is the template).
3. **Cozy moments** — Sleepy, sunbeam, wholesome stills.
4. **Play / zoomies** — Toys, hunting practice, chaos.
5. **Judging humans** — Close-ups of disapproval and side-eye.
6. **Rescue glow-up** — *The heart of the brand.* Throwback kitten/early photos paired with current confident shots; Sheldon-from-hiding-to-throne arcs; Amy-from-scared-to-sprawled moments.

## 5. Cadence & content math

| Platform | Cadence | Posting mechanism |
|---|---|---|
| Instagram feed | 4 posts/week | Vizard auto-post |
| Instagram Stories | Daily | Vizard auto-post (low-cost reposts from feed pool) |
| X | 4 posts/week | Vizard cross-post, mirrors IG feed |
| TikTok | 3 posts/week | **Semi-auto** — bot prepares video + caption + trending sound suggestion, sister taps post in TikTok app to preserve native sound access |

**Unique-asset need:** ~4 pieces/week (IG and X mirror each other; TikTok reworks the same week's content into Photo Mode or short video). Sister's existing stockpile (**216 photos + 131 videos**) gives ~3 months runway before she needs to add new content.

**Best posting times (CET, Stuttgart):**
- Weekdays: 08:00 (commute), 12:30 (lunch), 19:00 (dinner)
- Weekends: 10:00, 14:00, 20:00
- Initial schedule: IG feed Tue/Thu/Sat/Sun at 19:00 CET; X mirrors at 19:30 CET; TikTok Mon/Wed/Fri at 19:00 CET.

## 6. Architecture overview

```
                    ┌───────────────────────────────┐
                    │   Sneha's phone (sister)      │
                    │   Uploads photos/videos to    │
                    │   Google Drive folders        │
                    └──────────────┬────────────────┘
                                   │
                                   ▼
        ┌──────────────────────────────────────────────┐
        │  Google Drive — Shamy Content/                │
        │   00_inbox/                                   │
        │   01_safe_amy/    01_safe_sheldon/            │
        │   01_safe_both/   02_humans_in_frame/ (NEVER) │
        │   03_videos_raw/  04_ready/   99_posted/      │
        └──────────────┬───────────────────────────────┘
                       │ (read by pipeline)
                       ▼
   ┌─────────────────────────────────────────────────────────┐
   │  GitHub Actions cron (in MMW274/Shamy-social-media)     │
   │                                                          │
   │  1. Pick next slot from content calendar (JSON in repo) │
   │  2. Select matching asset(s) from safe folders          │
   │  3. Privacy check: Gemini Vision scans for humans       │
   │  4. Process: ffmpeg Ken Burns / AI animation / meme     │
   │  5. Generate caption + hashtags via Gemini (vision)     │
   │  6. Pick suggested trending sound (TikTok)              │
   │  7. Stage processed asset to Drive 04_ready/            │
   │  8. Send Telegram approval card to Sneha & Mehul        │
   └──────────────┬──────────────────────────────────────────┘
                  │
                  ▼
   ┌──────────────────────────────────────────────────────┐
   │  Telegram bot — approval card                         │
   │  [preview img/video] + [caption] + [#tags] + [sound]  │
   │  Buttons: ✅ Approve  ✏️ Edit  ⏭️ Skip  🚫 Block        │
   └──────────────┬───────────────────────────────────────┘
                  │ on ✅
                  ▼
   ┌─────────────────────┬──────────────────────────────────┐
   │ For IG + X:         │ For TikTok:                       │
   │  → Vizard.ai        │  → Bot sends ready video +        │
   │    Social Hub       │    caption + trending sound link  │
   │    auto-publishes   │    to Sneha's phone; she taps     │
   │                     │    post in TikTok app (preserves  │
   │                     │    native sound access).          │
   └─────────────────────┴──────────────────────────────────┘
                  │
                  ▼
   ┌─────────────────────────────────────────────────────────┐
   │  Pipeline moves used assets to 99_posted/ in Drive +     │
   │  logs post in content-log.jsonl in the repo (Git history │
   │  = version control for what was posted, when, where).    │
   └─────────────────────────────────────────────────────────┘
```

## 7. Privacy (Sneha & Anish)

**Two-layer enforcement — neither alone is sufficient:**

1. **Folder boundary (primary).** Sneha sorts every photo into `01_safe_*` or `02_humans_in_frame/` when she uploads. Pipeline only reads from `01_safe_*` and `03_videos_raw`. This is the contract.
2. **AI safety net (secondary).** Before *every* post, the asset is run through **Gemini Vision** with a prompt: *"Is there any human face, body part, or recognizable human element in this image/video frame? Answer strictly yes/no with confidence."* If yes or low-confidence-no, the asset is moved to `02_humans_in_frame/` and Telegram alerts Mehul.

For videos in `03_videos_raw`, Vizard's clipping output is run through the same Gemini check before posting.

A **dry-run mode** lets us replay the privacy check across the whole library on day 1 to catch any miscategorization before going live.

## 8. AI / tooling stack

| Need | Tool | Tier |
|---|---|---|
| Caption + hashtag generation (with vision) | **Gemini 2.5 Flash** via AI Studio API | Free (~1,500 req/day) |
| Privacy vision check | **Gemini 2.5 Flash** | Same free tier |
| Meme image edits | **Gemini 2.5 Flash Image** ("nano-banana") | Free tier |
| Subtle photo animation (Ken Burns) | **ffmpeg** | Free, no AI, runs in Actions |
| AI photo → video (hero posts only) | Rotate between **Kling**, **Pixverse**, **Hailuo (MiniMax)**, **Luma Dream Machine** | Each ~3–10 free credits/day; rotating extends quota |
| Long video → clipped Reels/TikToks | **Vizard.ai** | User has premium |
| Multi-platform publishing (IG + X) | **Vizard.ai Social Hub** | User has premium |
| Approval UX | **Telegram Bot API** | Free |
| Compute / cron | **GitHub Actions** | Free (2,000 min/mo private; this repo can be public) |
| Raw asset storage | **Google Drive** | Free (15 GB) |
| Code, configs, calendar, post log | **GitHub repo** [MMW274/Shamy-social-media](https://github.com/MMW274/Shamy-social-media) | Free |
| Secrets | GitHub Actions Secrets | Free |

**Animation rotation rule:** ~70% native photos + Vizard-clipped videos · ~20% Ken Burns subtle motion · ~10% AI-animated hero posts · memes sprinkled by Gemini Image when humor calls for it. Conserves free credits; avoids over-AI-ifying a brand whose strength is *real* cats.

## 9. Repo layout (in `MMW274/Shamy-social-media`)

```
.
├── README.md
├── .github/
│   └── workflows/
│       ├── daily-post.yml          # cron: pick + process + propose
│       ├── weekly-plan.yml         # cron: refresh content calendar
│       └── privacy-audit.yml       # one-off: scan all Drive assets
├── pipeline/
│   ├── select_asset.py             # picks next asset by pillar rotation
│   ├── privacy_check.py            # Gemini Vision human-detector
│   ├── caption_gen.py              # Gemini caption + hashtag
│   ├── animate.py                  # ffmpeg Ken Burns + AI animation API calls
│   ├── meme.py                     # Gemini Image meme edits
│   ├── publish_vizard.py           # Vizard Social Hub integration
│   ├── tiktok_handoff.py           # Telegram → manual post handoff
│   └── telegram_bot.py             # approval card + inline buttons
├── data/
│   ├── content-calendar.json       # planned posts: pillar, date, platform, status
│   ├── content-log.jsonl           # append-only record of every published post
│   ├── pillars.yaml                # pillar definitions, weights, sample caption seeds
│   ├── trending-sounds.yaml        # curated TikTok sounds, refreshed weekly
│   └── prompt-bank.md              # caption-style prompts for Gemini
└── docs/
    ├── superpowers/specs/2026-06-29-shamy-social-pipeline-design.md  # ← this file
    ├── runbook.md                  # what to do when something breaks
    └── sister-handoff.md           # one-page guide for Sneha (folders, Telegram)
```

## 10. Data flow per post

1. **08:00 CET cron** wakes up GitHub Action.
2. Reads `data/content-calendar.json`, finds slot for today/platform.
3. Pulls asset from `01_safe_*` or `03_videos_raw` in Drive matching the slot's pillar.
4. Runs `privacy_check.py` → Gemini Vision → blocks if human detected.
5. Runs `animate.py` per the slot's animation type (`native | ken_burns | ai_video | meme`).
6. Uploads processed file to `04_ready/`.
7. Runs `caption_gen.py` → Gemini sees the actual image, writes 1–3 caption variants in the chosen voice for the pillar.
8. For TikTok slots, picks suggested trending sound from `trending-sounds.yaml`.
9. Sends Telegram card to Sneha & Mehul: image preview, caption variants, hashtag set, and (for TikTok) sound link.
10. Sneha taps ✅ Approve / ✏️ Edit (opens caption in chat) / ⏭️ Skip (next asset proposed) / 🚫 Block (asset moved to humans folder).
11. On approve:
    - **IG + X:** call Vizard publish endpoint.
    - **TikTok:** Telegram sends Sneha the ready video, caption, and trending sound link; she taps post in the TikTok app.
12. Move source asset to `99_posted/`, append entry to `content-log.jsonl`, commit to repo.

## 11. Caption generation — the voice

Gemini receives:
- The actual image/video frame.
- The cat(s) in the image (from filename: `amy_*`, `sheldon_*`, `both_*`).
- The pillar.
- 5–10 voice examples for that pillar from `prompt-bank.md`.
- The instruction: *"Write 3 caption variants — 1 short (cat-POV), 1 medium (cat-POV with a joke), 1 narrator-style. End with 5–8 mixed hashtags: branded + niche."*

Sample voice seeds (illustrative):
- **Sibling chaos:** *"Sheldon: I require 3 meters of personal space. Amy: ✨ no ✨"*
- **Snack reactions:** *"Day 1 of strawberry diplomacy. The strawberry is winning."*
- **Cozy:** *"Off-duty. Do not disturb the loaf."*
- **Play:** *"Cardio."*
- **Judging humans:** *"You bought what, Anish."* — wait, that breaks privacy. Use *"You bought what."*
- **Rescue glow-up:** *"From hiding behind the couch to claiming the highest shelf. Sheldon, year three."*

**Hashtag strategy:** 5–8 tags max, mixing branded (`#LifeWithShamy #Shamy #AmyAndSheldon`) with niche (`#mainecoonsofinstagram #bengalcatsofinstagram #catsoftiktok #rescuecatsofinstagram #catsofgermany`).

## 12. Trending-sound strategy (TikTok)

- A weekly cron checks a curated list of pet-niche TikTok creators and notes which sounds appear repeatedly.
- A human-curated `trending-sounds.yaml` holds 10–20 sounds with tags (`upbeat`, `cozy`, `dramatic`, `funny`), refreshed weekly.
- Pipeline matches sound mood to pillar (cozy pillar → cozy sound, sibling chaos → dramatic, etc.).
- The Telegram TikTok handoff includes the **link to the sound in TikTok** so Sneha can tap it natively.

## 13. Error handling & graceful degradation

| Failure | Behavior |
|---|---|
| Gemini API down | Fall back to caption templates in `prompt-bank.md`; flag for Mehul review |
| AI animation API quota exhausted | Drop to Ken Burns animation; never block the post |
| Privacy check ambiguous | Always err on block → human review |
| Vizard publish fails | Telegram alerts Mehul; asset stays in `04_ready/` for retry |
| Drive auth expired | GitHub Action fails loudly; Mehul rotates token from runbook |
| No assets available for pillar slot | Bot sends Sneha a content-prompt nudge: *"We need a 'snack reaction' shot this week. Try Amy meeting an ice cube?"* |

## 14. MVP scope (what we build first)

To respect KISS, **v0.1 is intentionally tiny:**

- Drive folder structure created and seeded with 50 sister-sorted photos.
- Repo skeleton with `content-calendar.json` for next 2 weeks.
- `caption_gen.py` (Gemini) + `privacy_check.py` (Gemini Vision) working locally.
- Telegram bot with approval buttons.
- **Manual** final publishing for IG/X (we copy the Telegram-approved caption into Vizard's web UI ourselves) — confirms the content quality before wiring Vizard's API.
- TikTok handoff via Telegram works end-to-end.

**v0.2** wires Vizard's publishing API.
**v0.3** adds AI animation rotation + meme generation.
**v0.4** adds analytics dashboard (post log → simple chart).

## 15. Success criteria

- Sneha spends **≤ 5 minutes/day** on the project (just taps Telegram + posts the TikTok).
- **Zero** posts ever contain Sneha or Anish.
- 4-week test: pipeline reliably proposes ≥ 20 posts, ≥ 80% approve-rate (proxy for quality).
- Stretch: 500 IG followers / 200 X followers / first viral TikTok within 90 days.

## 16. Open questions / TBD

- Amy's exact age (to confirm with Sneha).
- TikTok handle availability check.
- Whether to set the GitHub repo to **public** (unlocks unlimited Actions minutes) or keep **private** (2,000 min/mo is still plenty for this workload).
- Will Sneha want her own Telegram approval channel, or will Mehul approve on her behalf during the first 2 weeks?

## 17. Out of scope (explicitly)

- Custom mobile app for Sneha — Telegram is enough.
- Merch / monetization — defer until 5k followers somewhere.
- Cross-pollinating with cat-influencer DMs — manual until there's signal.
- A web dashboard — JSON files in Git + Telegram is the UI.
