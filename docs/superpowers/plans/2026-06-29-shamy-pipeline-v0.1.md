# Shamy Pipeline v0.1 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a local-runnable MVP that picks an asset from Google Drive, runs a Gemini Vision privacy check, generates 3 caption variants + hashtags via Gemini, and sends a Telegram approval card to Sneha & Mehul. IG/X publishing is done manually via Vizard web UI in v0.1; TikTok hands off the ready video and trending sound to Sneha's phone for manual posting.

**Architecture:** A single Python package `pipeline/` with focused modules (config, brand-voice loader, drive client, privacy check, caption gen, asset selector, telegram bot, content log) glued together by a CLI runner. Logic modules are pure and TDD'd; I/O modules are smoke-tested with real APIs in dry-run mode. The same CLI runner is invoked by GitHub Actions cron in v0.2.

**Tech Stack:** Python 3.11, google-generativeai (Gemini), google-api-python-client (Drive), python-telegram-bot, PyYAML, pytest. Vizard is web-UI in v0.1; its API ships in v0.2.

---

## File structure (locked before tasks)

```
pipeline/
├── __init__.py
├── config.py              # env + .env loader, dataclass for all settings
├── brand.py               # loads & validates data/brand-voice.yaml
├── slots.py               # ContentSlot dataclass, pillar rotation logic
├── selector.py            # match Drive files to a slot
├── drive.py               # Google Drive auth + folder listing + move
├── privacy.py             # Gemini Vision "human in this image?" check
├── caption.py             # Gemini Vision caption + hashtag generation
├── telegram_bot.py        # approval card sender + button handlers
├── postlog.py             # append-only JSONL writer + duplicate guard
└── run.py                 # CLI entrypoint that wires it all up

tests/
├── __init__.py
├── test_brand.py
├── test_slots.py
├── test_selector.py
├── test_privacy.py
├── test_caption.py
├── test_postlog.py
└── fixtures/
    ├── sample_brand_voice.yaml
    ├── amy_window.jpg     # tiny test JPEG (placeholder generated)
    ├── sheldon_play.jpg
    └── humans_in_frame.jpg

data/
├── brand-design-system.md  # ✅ already written
├── brand-voice.yaml        # ✅ already written
├── free-apis-shortlist.md  # ✅ already written
├── content-calendar.json   # ← task 5
└── content-log.jsonl       # ← created on first run (empty initially)

docs/
├── superpowers/specs/2026-06-29-shamy-social-pipeline-design.md  # ✅
├── superpowers/plans/2026-06-29-shamy-pipeline-v0.1.md           # this file
├── runbook.md              # ← task 14
└── sister-handoff.md       # ← task 14
```

---

## Task 1: Set up local dev environment

**Files:**
- Create: `pipeline/__init__.py` (empty — already created)
- Create: `pyproject.toml`
- Verify: `requirements.txt` (already created)

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "shamy-pipeline"
version = "0.1.0"
description = "Shamy social media pipeline — Amy & Sheldon"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v"

[tool.ruff]
line-length = 100
target-version = "py311"
```

- [ ] **Step 2: Create venv and install**

Run:
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
Expected: all packages install without conflict.

- [ ] **Step 3: Smoke-test imports**

Run:
```bash
python -c "import google.generativeai, googleapiclient, telegram, yaml, dotenv, PIL; print('ok')"
```
Expected: prints `ok`.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add pyproject and verify dev env"
```

---

## Task 2: `pipeline/config.py` — settings loader

**Files:**
- Create: `pipeline/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the failing test**

`tests/test_config.py`:
```python
import os
from pipeline.config import Settings, load_settings


def test_load_settings_from_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g-key")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t-tok")
    monkeypatch.setenv("TELEGRAM_CHAT_ID_SNEHA", "111")
    monkeypatch.setenv("TELEGRAM_CHAT_ID_MEHUL", "222")
    monkeypatch.setenv("DRIVE_ROOT_FOLDER_ID", "abc")
    monkeypatch.setenv("DRY_RUN", "true")

    s = load_settings()
    assert isinstance(s, Settings)
    assert s.gemini_api_key == "g-key"
    assert s.telegram_bot_token == "t-tok"
    assert s.dry_run is True
    assert s.timezone == "Europe/Berlin"


def test_missing_required_raises(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    import pytest
    with pytest.raises(RuntimeError) as exc:
        load_settings()
    assert "GEMINI_API_KEY" in str(exc.value)
```

- [ ] **Step 2: Run test, verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: pipeline.config`.

- [ ] **Step 3: Write minimal implementation**

`pipeline/config.py`:
```python
"""Pipeline configuration loaded from environment."""
from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv


REQUIRED = [
    "GEMINI_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID_SNEHA",
    "TELEGRAM_CHAT_ID_MEHUL",
    "DRIVE_ROOT_FOLDER_ID",
]


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    telegram_bot_token: str
    telegram_chat_id_sneha: int
    telegram_chat_id_mehul: int
    drive_root_folder_id: str
    google_credentials_json: str
    vizard_api_key: str
    timezone: str
    dry_run: bool
    log_level: str


def load_settings() -> Settings:
    load_dotenv()
    missing = [k for k in REQUIRED if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")

    return Settings(
        gemini_api_key=os.environ["GEMINI_API_KEY"],
        telegram_bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
        telegram_chat_id_sneha=int(os.environ["TELEGRAM_CHAT_ID_SNEHA"]),
        telegram_chat_id_mehul=int(os.environ["TELEGRAM_CHAT_ID_MEHUL"]),
        drive_root_folder_id=os.environ["DRIVE_ROOT_FOLDER_ID"],
        google_credentials_json=os.getenv("GOOGLE_CREDENTIALS_JSON", ""),
        vizard_api_key=os.getenv("VIZARD_API_KEY", ""),
        timezone=os.getenv("TZ", "Europe/Berlin"),
        dry_run=os.getenv("DRY_RUN", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
```

- [ ] **Step 4: Run tests, verify pass**

Run: `pytest tests/test_config.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add pipeline/config.py tests/test_config.py
git commit -m "feat(config): env-driven Settings loader with required-var validation"
```

---

## Task 3: `pipeline/brand.py` — brand voice loader

**Files:**
- Create: `pipeline/brand.py`
- Create: `tests/test_brand.py`
- Create: `tests/fixtures/sample_brand_voice.yaml`

- [ ] **Step 1: Write fixture**

`tests/fixtures/sample_brand_voice.yaml`:
```yaml
brand:
  name: Shamy
  tagline: Test tagline
cats:
  amy:
    aka: ["Amy"]
    look: fluffy
    personality: ["active"]
    voice_traits: ["dramatic"]
    catchphrases: ["meow"]
  sheldon:
    aka: ["Sheldon"]
    look: spotted
    personality: ["cautious"]
    voice_traits: ["observational"]
    catchphrases: ["reviewed"]
voice:
  primary: cat-POV first person
  language: English only
  do: ["use observational humor"]
  do_not: ["beg for likes"]
privacy:
  forbidden_terms_in_captions: ["Sneha", "Anish"]
pillars:
  cozy:
    description: "Sleepy"
    example_captions: ["Off-duty."]
    typical_hashtags: ["#CatLoaf"]
hashtag_bank:
  branded_always_include_one: ["#LifeWithShamy"]
caption_generation_rules:
  required_outputs_per_request: 3
  hashtag_count: [5, 8]
```

- [ ] **Step 2: Write the failing test**

`tests/test_brand.py`:
```python
from pathlib import Path
from pipeline.brand import BrandVoice, load_brand_voice


FIXTURE = Path(__file__).parent / "fixtures" / "sample_brand_voice.yaml"


def test_loads_basic_fields():
    bv = load_brand_voice(FIXTURE)
    assert isinstance(bv, BrandVoice)
    assert bv.brand_name == "Shamy"
    assert "Amy" in bv.cats
    assert "Sheldon" in bv.cats
    assert bv.cats["Sheldon"].personality == ["cautious"]


def test_pillar_lookup():
    bv = load_brand_voice(FIXTURE)
    assert "cozy" in bv.pillars
    assert bv.pillars["cozy"].description == "Sleepy"


def test_forbidden_terms_present():
    bv = load_brand_voice(FIXTURE)
    assert "Sneha" in bv.forbidden_terms
    assert "Anish" in bv.forbidden_terms


def test_real_brand_voice_loads():
    real = Path(__file__).parents[1] / "data" / "brand-voice.yaml"
    bv = load_brand_voice(real)
    assert bv.brand_name == "Shamy"
    assert len(bv.pillars) >= 6
```

- [ ] **Step 3: Run test, verify it fails**

Run: `pytest tests/test_brand.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 4: Write minimal implementation**

`pipeline/brand.py`:
```python
"""Loads and validates data/brand-voice.yaml into a typed config."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class CatProfile:
    aka: list[str]
    look: str
    personality: list[str]
    voice_traits: list[str]
    catchphrases: list[str]


@dataclass(frozen=True)
class Pillar:
    description: str
    example_captions: list[str]
    typical_hashtags: list[str]
    voice_override: str | None = None


@dataclass(frozen=True)
class BrandVoice:
    brand_name: str
    tagline: str
    cats: dict[str, CatProfile]
    voice_primary: str
    voice_do: list[str]
    voice_do_not: list[str]
    forbidden_terms: list[str]
    pillars: dict[str, Pillar]
    branded_hashtags: list[str]
    hashtag_count_min: int
    hashtag_count_max: int
    raw: dict = field(default_factory=dict)


def load_brand_voice(path: Path | str) -> BrandVoice:
    data = yaml.safe_load(Path(path).read_text())

    cats = {}
    for key, name in (("amy", "Amy"), ("sheldon", "Sheldon")):
        c = data["cats"][key]
        cats[name] = CatProfile(
            aka=c.get("aka", []),
            look=c.get("look", ""),
            personality=c.get("personality", []),
            voice_traits=c.get("voice_traits", []),
            catchphrases=c.get("catchphrases", []),
        )

    pillars = {
        name: Pillar(
            description=p.get("description", ""),
            example_captions=p.get("example_captions", []),
            typical_hashtags=p.get("typical_hashtags", []),
            voice_override=p.get("voice_override"),
        )
        for name, p in data.get("pillars", {}).items()
    }

    rules = data.get("caption_generation_rules", {})
    hc = rules.get("hashtag_count", [5, 8])

    return BrandVoice(
        brand_name=data["brand"]["name"],
        tagline=data["brand"].get("tagline", ""),
        cats=cats,
        voice_primary=data["voice"]["primary"],
        voice_do=data["voice"].get("do", []),
        voice_do_not=data["voice"].get("do_not", []),
        forbidden_terms=data.get("privacy", {}).get("forbidden_terms_in_captions", []),
        pillars=pillars,
        branded_hashtags=data.get("hashtag_bank", {}).get("branded_always_include_one", []),
        hashtag_count_min=int(hc[0]),
        hashtag_count_max=int(hc[1]),
        raw=data,
    )
```

- [ ] **Step 5: Run tests, verify pass**

Run: `pytest tests/test_brand.py -v`
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add pipeline/brand.py tests/test_brand.py tests/fixtures/sample_brand_voice.yaml
git commit -m "feat(brand): typed loader for brand-voice.yaml with fixture-driven tests"
```

---

## Task 4: `pipeline/slots.py` — content slot + pillar rotation

**Files:**
- Create: `pipeline/slots.py`
- Create: `tests/test_slots.py`

- [ ] **Step 1: Write the failing test**

`tests/test_slots.py`:
```python
from datetime import date
from pipeline.slots import (
    ContentSlot,
    Platform,
    PostStatus,
    rotate_pillars,
    slot_from_dict,
)


def test_rotation_cycles_through_pillars():
    pillars = ["sibling_chaos", "snack_reactions", "cozy", "play_zoomies", "judging_humans", "rescue_glow_up"]
    seq = rotate_pillars(pillars, start_index=0, n=8)
    assert seq[0] == "sibling_chaos"
    assert seq[6] == "sibling_chaos"
    assert seq[7] == "snack_reactions"


def test_rotation_respects_start_index():
    pillars = ["a", "b", "c"]
    seq = rotate_pillars(pillars, start_index=2, n=4)
    assert seq == ["c", "a", "b", "c"]


def test_slot_from_dict_round_trip():
    raw = {
        "id": "2026-07-01-ig",
        "date": "2026-07-01",
        "platform": "instagram",
        "pillar": "cozy",
        "status": "planned",
    }
    s = slot_from_dict(raw)
    assert s.id == "2026-07-01-ig"
    assert s.date == date(2026, 7, 1)
    assert s.platform == Platform.INSTAGRAM
    assert s.status == PostStatus.PLANNED


def test_slot_invalid_platform_raises():
    import pytest
    bad = {"id": "x", "date": "2026-07-01", "platform": "facebook", "pillar": "cozy", "status": "planned"}
    with pytest.raises(ValueError):
        slot_from_dict(bad)
```

- [ ] **Step 2: Run test, verify it fails**

Run: `pytest tests/test_slots.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

`pipeline/slots.py`:
```python
"""Content slot data model + pillar rotation logic."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class Platform(Enum):
    INSTAGRAM = "instagram"
    X = "x"
    TIKTOK = "tiktok"


class PostStatus(Enum):
    PLANNED = "planned"
    PROPOSED = "proposed"
    APPROVED = "approved"
    POSTED = "posted"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


@dataclass
class ContentSlot:
    id: str
    date: date
    platform: Platform
    pillar: str
    status: PostStatus
    asset_path: str | None = None
    caption: str | None = None
    hashtags: list[str] | None = None
    sound_url: str | None = None


def rotate_pillars(pillars: list[str], start_index: int, n: int) -> list[str]:
    """Return n pillar names cycling through `pillars`, starting at start_index."""
    if not pillars:
        raise ValueError("pillars list cannot be empty")
    return [pillars[(start_index + i) % len(pillars)] for i in range(n)]


def slot_from_dict(d: dict) -> ContentSlot:
    return ContentSlot(
        id=d["id"],
        date=date.fromisoformat(d["date"]),
        platform=Platform(d["platform"]),
        pillar=d["pillar"],
        status=PostStatus(d.get("status", "planned")),
        asset_path=d.get("asset_path"),
        caption=d.get("caption"),
        hashtags=d.get("hashtags"),
        sound_url=d.get("sound_url"),
    )
```

- [ ] **Step 4: Run tests, verify pass**

Run: `pytest tests/test_slots.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add pipeline/slots.py tests/test_slots.py
git commit -m "feat(slots): ContentSlot model + pillar rotation"
```

---

## Task 5: Seed `data/content-calendar.json` for two weeks

**Files:**
- Create: `data/content-calendar.json`

- [ ] **Step 1: Write the calendar**

Cadence (from spec §5): IG Tue/Thu/Sat/Sun 19:00 CET, X mirrors IG 19:30 CET, TikTok Mon/Wed/Fri 19:00 CET.

Start date: Monday next week. Use dates 2026-07-06 through 2026-07-19.

`data/content-calendar.json`:
```json
{
  "version": 1,
  "timezone": "Europe/Berlin",
  "default_pillars": [
    "sibling_chaos",
    "snack_reactions",
    "cozy",
    "play_zoomies",
    "judging_humans",
    "rescue_glow_up"
  ],
  "slots": [
    { "id": "2026-07-06-tt", "date": "2026-07-06", "platform": "tiktok",    "pillar": "sibling_chaos",  "status": "planned" },
    { "id": "2026-07-07-ig", "date": "2026-07-07", "platform": "instagram", "pillar": "snack_reactions","status": "planned" },
    { "id": "2026-07-07-x",  "date": "2026-07-07", "platform": "x",         "pillar": "snack_reactions","status": "planned" },
    { "id": "2026-07-08-tt", "date": "2026-07-08", "platform": "tiktok",    "pillar": "cozy",           "status": "planned" },
    { "id": "2026-07-09-ig", "date": "2026-07-09", "platform": "instagram", "pillar": "play_zoomies",   "status": "planned" },
    { "id": "2026-07-09-x",  "date": "2026-07-09", "platform": "x",         "pillar": "play_zoomies",   "status": "planned" },
    { "id": "2026-07-10-tt", "date": "2026-07-10", "platform": "tiktok",    "pillar": "judging_humans", "status": "planned" },
    { "id": "2026-07-11-ig", "date": "2026-07-11", "platform": "instagram", "pillar": "rescue_glow_up", "status": "planned" },
    { "id": "2026-07-11-x",  "date": "2026-07-11", "platform": "x",         "pillar": "rescue_glow_up", "status": "planned" },
    { "id": "2026-07-12-ig", "date": "2026-07-12", "platform": "instagram", "pillar": "sibling_chaos",  "status": "planned" },
    { "id": "2026-07-12-x",  "date": "2026-07-12", "platform": "x",         "pillar": "sibling_chaos",  "status": "planned" },

    { "id": "2026-07-13-tt", "date": "2026-07-13", "platform": "tiktok",    "pillar": "snack_reactions","status": "planned" },
    { "id": "2026-07-14-ig", "date": "2026-07-14", "platform": "instagram", "pillar": "cozy",           "status": "planned" },
    { "id": "2026-07-14-x",  "date": "2026-07-14", "platform": "x",         "pillar": "cozy",           "status": "planned" },
    { "id": "2026-07-15-tt", "date": "2026-07-15", "platform": "tiktok",    "pillar": "play_zoomies",   "status": "planned" },
    { "id": "2026-07-16-ig", "date": "2026-07-16", "platform": "instagram", "pillar": "judging_humans", "status": "planned" },
    { "id": "2026-07-16-x",  "date": "2026-07-16", "platform": "x",         "pillar": "judging_humans", "status": "planned" },
    { "id": "2026-07-17-tt", "date": "2026-07-17", "platform": "tiktok",    "pillar": "rescue_glow_up", "status": "planned" },
    { "id": "2026-07-18-ig", "date": "2026-07-18", "platform": "instagram", "pillar": "sibling_chaos",  "status": "planned" },
    { "id": "2026-07-18-x",  "date": "2026-07-18", "platform": "x",         "pillar": "sibling_chaos",  "status": "planned" },
    { "id": "2026-07-19-ig", "date": "2026-07-19", "platform": "instagram", "pillar": "snack_reactions","status": "planned" },
    { "id": "2026-07-19-x",  "date": "2026-07-19", "platform": "x",         "pillar": "snack_reactions","status": "planned" }
  ]
}
```

- [ ] **Step 2: Verify JSON parses**

Run: `python -c "import json,pathlib; json.loads(pathlib.Path('data/content-calendar.json').read_text()); print('ok')"`
Expected: prints `ok`.

- [ ] **Step 3: Commit**

```bash
git add data/content-calendar.json
git commit -m "feat(data): seed 2-week content calendar with cadence-correct slots"
```

---

## Task 6: `pipeline/postlog.py` — append-only post log

**Files:**
- Create: `pipeline/postlog.py`
- Create: `tests/test_postlog.py`

- [ ] **Step 1: Write the failing test**

`tests/test_postlog.py`:
```python
import json
from pathlib import Path
from datetime import datetime, timezone
from pipeline.postlog import PostRecord, append_record, is_duplicate, load_all


def test_append_and_load(tmp_path: Path):
    log = tmp_path / "log.jsonl"
    rec = PostRecord(
        slot_id="2026-07-07-ig",
        platform="instagram",
        pillar="cozy",
        asset_path="01_safe_amy/img_001.jpg",
        caption="Off-duty.",
        hashtags=["#LifeWithShamy", "#CatLoaf"],
        timestamp_utc=datetime(2026, 7, 7, 17, 0, tzinfo=timezone.utc),
        sound_url=None,
        external_post_id=None,
    )
    append_record(log, rec)
    records = load_all(log)
    assert len(records) == 1
    assert records[0].slot_id == "2026-07-07-ig"


def test_duplicate_detected_by_slot_id(tmp_path: Path):
    log = tmp_path / "log.jsonl"
    rec = PostRecord(
        slot_id="2026-07-07-ig",
        platform="instagram",
        pillar="cozy",
        asset_path="x.jpg",
        caption="c",
        hashtags=[],
        timestamp_utc=datetime(2026, 7, 7, tzinfo=timezone.utc),
        sound_url=None,
        external_post_id=None,
    )
    append_record(log, rec)
    assert is_duplicate(log, "2026-07-07-ig") is True
    assert is_duplicate(log, "2026-07-08-ig") is False


def test_missing_log_returns_empty(tmp_path: Path):
    assert load_all(tmp_path / "nope.jsonl") == []
    assert is_duplicate(tmp_path / "nope.jsonl", "anything") is False


def test_record_serializes_iso_timestamp(tmp_path: Path):
    log = tmp_path / "log.jsonl"
    rec = PostRecord(
        slot_id="s",
        platform="x",
        pillar="cozy",
        asset_path="a.jpg",
        caption="hi",
        hashtags=["#a"],
        timestamp_utc=datetime(2026, 7, 7, 12, 30, tzinfo=timezone.utc),
        sound_url=None,
        external_post_id=None,
    )
    append_record(log, rec)
    line = log.read_text().strip()
    parsed = json.loads(line)
    assert parsed["timestamp_utc"] == "2026-07-07T12:30:00+00:00"
```

- [ ] **Step 2: Run test, verify it fails**

Run: `pytest tests/test_postlog.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

`pipeline/postlog.py`:
```python
"""Append-only JSONL log of posted content. Single source of truth for what's gone out."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class PostRecord:
    slot_id: str
    platform: str
    pillar: str
    asset_path: str
    caption: str
    hashtags: list[str]
    timestamp_utc: datetime
    sound_url: str | None
    external_post_id: str | None


def _to_dict(rec: PostRecord) -> dict:
    d = asdict(rec)
    d["timestamp_utc"] = rec.timestamp_utc.isoformat()
    return d


def _from_dict(d: dict) -> PostRecord:
    return PostRecord(
        slot_id=d["slot_id"],
        platform=d["platform"],
        pillar=d["pillar"],
        asset_path=d["asset_path"],
        caption=d["caption"],
        hashtags=d["hashtags"],
        timestamp_utc=datetime.fromisoformat(d["timestamp_utc"]),
        sound_url=d.get("sound_url"),
        external_post_id=d.get("external_post_id"),
    )


def append_record(path: Path | str, rec: PostRecord) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(_to_dict(rec)) + "\n")


def load_all(path: Path | str) -> list[PostRecord]:
    path = Path(path)
    if not path.exists():
        return []
    out: list[PostRecord] = []
    for line in path.read_text().splitlines():
        if line.strip():
            out.append(_from_dict(json.loads(line)))
    return out


def is_duplicate(path: Path | str, slot_id: str) -> bool:
    return any(r.slot_id == slot_id for r in load_all(path))
```

- [ ] **Step 4: Run tests, verify pass**

Run: `pytest tests/test_postlog.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add pipeline/postlog.py tests/test_postlog.py
git commit -m "feat(postlog): JSONL post log with duplicate guard"
```

---

## Task 7: `pipeline/selector.py` — match Drive files to a slot

**Files:**
- Create: `pipeline/selector.py`
- Create: `tests/test_selector.py`

The selector takes a slot's pillar + the cat hint and a list of `DriveFile` objects, returns the best candidate. Filename conventions:
- `01_safe_amy/...` → Amy only
- `01_safe_sheldon/...` → Sheldon only
- `01_safe_both/...` → both
- Filenames may include a tag: `amy_window_001.jpg`, `sheldon_snack_002.jpg`, `both_play_003.jpg`.

The selector excludes already-used assets (looked up in the post log) and picks the oldest-by-name match for predictability.

- [ ] **Step 1: Write the failing test**

`tests/test_selector.py`:
```python
from pipeline.selector import DriveFile, select_asset


def make(name, folder, used=False):
    return DriveFile(id=name, name=name, folder=folder, mime_type="image/jpeg")


def test_picks_pillar_matching_file_for_amy_pillar():
    files = [
        make("amy_cozy_001.jpg", "01_safe_amy"),
        make("amy_play_002.jpg", "01_safe_amy"),
        make("amy_cozy_003.jpg", "01_safe_amy"),
    ]
    pick = select_asset(files, pillar="cozy", used_ids=set())
    assert pick is not None
    assert pick.name == "amy_cozy_001.jpg"


def test_skips_used_assets():
    files = [
        make("amy_cozy_001.jpg", "01_safe_amy"),
        make("amy_cozy_002.jpg", "01_safe_amy"),
    ]
    pick = select_asset(files, pillar="cozy", used_ids={"amy_cozy_001.jpg"})
    assert pick.name == "amy_cozy_002.jpg"


def test_returns_none_when_no_match():
    files = [make("amy_play_001.jpg", "01_safe_amy")]
    pick = select_asset(files, pillar="cozy", used_ids=set())
    assert pick is None


def test_rescue_glow_up_falls_back_to_any_safe_asset():
    files = [
        make("amy_window_001.jpg", "01_safe_amy"),
        make("sheldon_throne_002.jpg", "01_safe_sheldon"),
    ]
    pick = select_asset(files, pillar="rescue_glow_up", used_ids=set())
    assert pick is not None


def test_excludes_humans_folder_even_if_filename_matches():
    files = [
        make("amy_cozy_001.jpg", "02_humans_in_frame"),
        make("amy_cozy_002.jpg", "01_safe_amy"),
    ]
    pick = select_asset(files, pillar="cozy", used_ids=set())
    assert pick.folder == "01_safe_amy"
```

- [ ] **Step 2: Run test, verify it fails**

Run: `pytest tests/test_selector.py -v`
Expected: FAIL `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

`pipeline/selector.py`:
```python
"""Select the best Drive asset for a given content slot."""
from __future__ import annotations

from dataclasses import dataclass


SAFE_FOLDERS = {"01_safe_amy", "01_safe_sheldon", "01_safe_both", "03_videos_raw"}
HUMAN_FOLDER = "02_humans_in_frame"

PILLAR_KEYWORDS: dict[str, list[str]] = {
    "sibling_chaos": ["both", "siblings", "fight", "share", "chaos"],
    "snack_reactions": ["snack", "treat", "food", "strawberry", "apple", "fruit"],
    "cozy": ["cozy", "sleep", "loaf", "sun", "nap", "sleepy", "window"],
    "play_zoomies": ["play", "zoomies", "toy", "hunt", "jump", "play"],
    "judging_humans": ["judge", "judgy", "side-eye", "stare", "disapprove"],
    "rescue_glow_up": ["throwback", "kitten", "young", "before", "glowup"],
}


@dataclass(frozen=True)
class DriveFile:
    id: str
    name: str
    folder: str
    mime_type: str


def select_asset(
    files: list[DriveFile],
    pillar: str,
    used_ids: set[str],
) -> DriveFile | None:
    safe = [
        f for f in files
        if f.folder in SAFE_FOLDERS and f.folder != HUMAN_FOLDER and f.id not in used_ids
    ]
    if not safe:
        return None

    keywords = PILLAR_KEYWORDS.get(pillar, [])
    matches = [f for f in safe if any(k in f.name.lower() for k in keywords)]

    candidates = matches if matches else (safe if pillar == "rescue_glow_up" else [])
    if not candidates:
        return None

    return sorted(candidates, key=lambda f: f.name)[0]
```

- [ ] **Step 4: Run tests, verify pass**

Run: `pytest tests/test_selector.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add pipeline/selector.py tests/test_selector.py
git commit -m "feat(selector): pillar-keyword asset matching with used-id exclusion"
```

---

## Task 8: `pipeline/drive.py` — Google Drive client

**Files:**
- Create: `pipeline/drive.py`
- Create: `tests/test_drive_smoke.py`

Drive code is mostly thin wrappers around the SDK; we smoke-test rather than mock-test because the value is "does the auth and listing actually work."

- [ ] **Step 1: Set up Google Drive OAuth credentials**

Manual one-time setup (document in `docs/runbook.md`):
1. Go to https://console.cloud.google.com/, create a project "Shamy Pipeline".
2. Enable Google Drive API.
3. Create OAuth client (Desktop app), download `credentials.json` to repo root (gitignored).
4. Run a one-time auth script to get a refresh token (this step's deliverable).

- [ ] **Step 2: Write the auth helper**

`pipeline/drive.py`:
```python
"""Google Drive client — list a folder, download files, move files between folders."""
from __future__ import annotations

import io
import json
import os
from dataclasses import dataclass
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive"]

DEFAULT_TOKEN_PATH = Path("token.json")
DEFAULT_CREDS_PATH = Path("credentials.json")


@dataclass(frozen=True)
class DriveFile:
    id: str
    name: str
    folder: str
    mime_type: str


def authorize(
    creds_path: Path = DEFAULT_CREDS_PATH,
    token_path: Path = DEFAULT_TOKEN_PATH,
):
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())
    return build("drive", "v3", credentials=creds)


def list_folder_recursive(service, root_folder_id: str) -> list[DriveFile]:
    """Walk subfolders one level (01_safe_amy, 01_safe_sheldon, etc.) and list files."""
    folders = _list_subfolders(service, root_folder_id)
    files: list[DriveFile] = []
    for f_id, f_name in folders.items():
        page_token = None
        while True:
            resp = service.files().list(
                q=f"'{f_id}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false",
                fields="nextPageToken, files(id, name, mimeType)",
                pageToken=page_token,
                pageSize=200,
            ).execute()
            for item in resp.get("files", []):
                files.append(
                    DriveFile(
                        id=item["id"],
                        name=item["name"],
                        folder=f_name,
                        mime_type=item["mimeType"],
                    )
                )
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
    return files


def _list_subfolders(service, parent_id: str) -> dict[str, str]:
    resp = service.files().list(
        q=f"'{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
        fields="files(id, name)",
        pageSize=100,
    ).execute()
    return {item["id"]: item["name"] for item in resp.get("files", [])}


def download_file(service, file_id: str, dest: Path) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = service.files().get_media(fileId=file_id)
    with dest.open("wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    return dest


def move_file(service, file_id: str, new_parent_folder_id: str) -> None:
    file = service.files().get(fileId=file_id, fields="parents").execute()
    previous_parents = ",".join(file.get("parents", []))
    service.files().update(
        fileId=file_id,
        addParents=new_parent_folder_id,
        removeParents=previous_parents,
        fields="id, parents",
    ).execute()
```

- [ ] **Step 3: Write smoke test (skipped when creds absent)**

`tests/test_drive_smoke.py`:
```python
import os
from pathlib import Path
import pytest

from pipeline.drive import authorize, list_folder_recursive


@pytest.mark.skipif(
    not Path("credentials.json").exists() or not os.getenv("DRIVE_ROOT_FOLDER_ID"),
    reason="Drive credentials not set up locally",
)
def test_can_list_root_folder():
    svc = authorize()
    files = list_folder_recursive(svc, os.environ["DRIVE_ROOT_FOLDER_ID"])
    folders = {f.folder for f in files}
    assert any(name.startswith("01_safe") for name in folders), folders
```

- [ ] **Step 4: Run smoke test**

Run: `pytest tests/test_drive_smoke.py -v`
Expected: PASS (if creds set up) or SKIPPED.

- [ ] **Step 5: Commit**

```bash
git add pipeline/drive.py tests/test_drive_smoke.py
git commit -m "feat(drive): Google Drive client with auth, listing, download, move"
```

---

## Task 9: `pipeline/privacy.py` — Gemini Vision human-detector

**Files:**
- Create: `pipeline/privacy.py`
- Create: `tests/test_privacy_smoke.py`

- [ ] **Step 1: Write implementation**

`pipeline/privacy.py`:
```python
"""Privacy check: does this image/video frame contain a human?

Layer 2 of two-layer privacy defense (layer 1 = Drive folder boundary).
Uses the new google-genai SDK (the legacy google-generativeai is EOL).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from google import genai
from PIL import Image


PROMPT = (
    "You are a privacy gatekeeper for a cat-content social media account. "
    "Examine this image. Is there ANY identifiable human element visible — "
    "a face, body part (hand, arm, leg, foot), or clearly human silhouette? "
    "Reflections, blurred humans, or partial humans also count.\n\n"
    "Respond in this exact format on a single line:\n"
    "VERDICT=<YES|NO|UNSURE> CONFIDENCE=<0.0-1.0> REASON=<short reason>"
)

MODEL_NAME = "gemini-2.5-flash"

# Module-level client, initialised by `configure()`.
_client: genai.Client | None = None


@dataclass(frozen=True)
class PrivacyVerdict:
    has_human: bool
    confidence: float
    reason: str
    raw: str


def configure(api_key: str) -> None:
    global _client
    _client = genai.Client(api_key=api_key)


def check_image(path: Path | str) -> PrivacyVerdict:
    if _client is None:
        raise RuntimeError("privacy.configure(api_key) must be called first")
    img = Image.open(path)
    resp = _client.models.generate_content(model=MODEL_NAME, contents=[PROMPT, img])
    text = (resp.text or "").strip()
    return _parse_verdict(text)


def _parse_verdict(text: str) -> PrivacyVerdict:
    verdict_str, conf, reason = "UNSURE", 0.0, text
    for token in text.replace("\n", " ").split():
        if token.startswith("VERDICT="):
            verdict_str = token.split("=", 1)[1].upper().strip(",")
        elif token.startswith("CONFIDENCE="):
            try:
                conf = float(token.split("=", 1)[1].strip(","))
            except ValueError:
                conf = 0.0
    if "REASON=" in text:
        reason = text.split("REASON=", 1)[1].strip()

    has_human = verdict_str == "YES" or (verdict_str == "UNSURE" and conf > 0.4)
    return PrivacyVerdict(has_human=has_human, confidence=conf, reason=reason, raw=text)


def is_safe_to_post(verdict: PrivacyVerdict, min_no_confidence: float = 0.7) -> bool:
    """Returns True only when the model says NO with high confidence."""
    if verdict.has_human:
        return False
    return verdict.confidence >= min_no_confidence
```

- [ ] **Step 2: Unit-test the parser**

`tests/test_privacy_smoke.py`:
```python
import os
from pathlib import Path
import pytest

from pipeline.privacy import _parse_verdict, is_safe_to_post, configure, check_image


def test_parses_yes_high_conf():
    v = _parse_verdict("VERDICT=YES CONFIDENCE=0.95 REASON=Hand visible in lower-right")
    assert v.has_human is True
    assert v.confidence == 0.95


def test_parses_no_high_conf():
    v = _parse_verdict("VERDICT=NO CONFIDENCE=0.98 REASON=Only the cat is visible")
    assert v.has_human is False
    assert is_safe_to_post(v) is True


def test_unsure_treated_conservatively():
    v = _parse_verdict("VERDICT=UNSURE CONFIDENCE=0.5 REASON=Possible reflection")
    assert v.has_human is True
    assert is_safe_to_post(v) is False


def test_low_confidence_no_still_blocked():
    v = _parse_verdict("VERDICT=NO CONFIDENCE=0.5 REASON=Ambiguous")
    assert v.has_human is False
    assert is_safe_to_post(v) is False


@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="No Gemini key")
def test_smoke_against_real_image():
    configure(os.environ["GEMINI_API_KEY"])
    fixture = Path("tests/fixtures/amy_window.jpg")
    if not fixture.exists():
        pytest.skip("No fixture image yet")
    v = check_image(fixture)
    assert v.raw  # got *some* response
```

- [ ] **Step 3: Run unit tests, verify pass**

Run: `pytest tests/test_privacy_smoke.py -v -k "not smoke"`
Expected: 4 passed.

- [ ] **Step 4: Commit**

```bash
git add pipeline/privacy.py tests/test_privacy_smoke.py
git commit -m "feat(privacy): Gemini Vision human-detector with conservative safe-to-post gate"
```

---

## Task 10: `pipeline/caption.py` — caption + hashtag generation

**Files:**
- Create: `pipeline/caption.py`
- Create: `tests/test_caption.py`

- [ ] **Step 1: Write the failing test**

`tests/test_caption.py`:
```python
from pathlib import Path
from pipeline.brand import load_brand_voice
from pipeline.caption import build_prompt, CaptionResult, validate_caption


BV = load_brand_voice(Path("data/brand-voice.yaml"))


def test_prompt_mentions_pillar_and_cat():
    prompt = build_prompt(BV, pillar="cozy", cat="Amy")
    assert "cozy" in prompt.lower()
    assert "Amy" in prompt
    assert "Sneha" in prompt or "forbidden" in prompt.lower()


def test_prompt_includes_voice_dos_and_donts():
    prompt = build_prompt(BV, pillar="snack_reactions", cat="Sheldon")
    assert "do not" in prompt.lower() or "avoid" in prompt.lower()


def test_validate_rejects_forbidden_terms():
    res = CaptionResult(
        variants=["Sneha and the cat had a moment."],
        hashtags=["#LifeWithShamy", "#CatLoaf"],
    )
    issues = validate_caption(res, BV)
    assert any("forbidden" in i.lower() for i in issues)


def test_validate_rejects_too_few_hashtags():
    res = CaptionResult(
        variants=["A short one."],
        hashtags=["#LifeWithShamy"],
    )
    issues = validate_caption(res, BV)
    assert any("hashtag" in i.lower() for i in issues)


def test_validate_passes_clean_result():
    res = CaptionResult(
        variants=["Off-duty.", "Slow blink technology.", "The loaf has assembled."],
        hashtags=["#LifeWithShamy", "#CatLoaf", "#MaineCoonsOfInstagram",
                  "#CatsOfGermany", "#CozyCats"],
    )
    issues = validate_caption(res, BV)
    assert issues == []
```

- [ ] **Step 2: Run test, verify fails**

Run: `pytest tests/test_caption.py -v`
Expected: FAIL `ModuleNotFoundError`.

- [ ] **Step 3: Write implementation**

`pipeline/caption.py`:
```python
"""Generate 3 caption variants + hashtag set using Gemini Vision (google-genai SDK)."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from google import genai
from PIL import Image

from pipeline.brand import BrandVoice

MODEL_NAME = "gemini-2.5-flash"
_client: genai.Client | None = None


@dataclass(frozen=True)
class CaptionResult:
    variants: list[str]
    hashtags: list[str]


def build_prompt(bv: BrandVoice, pillar: str, cat: str) -> str:
    pillar_obj = bv.pillars[pillar]
    do_list = "\n".join(f"- {x}" for x in bv.voice_do)
    dont_list = "\n".join(f"- {x}" for x in bv.voice_do_not)
    forbidden = ", ".join(bv.forbidden_terms)
    example = "\n".join(f"- {x}" for x in pillar_obj.example_captions[:3])
    pillar_tags = ", ".join(pillar_obj.typical_hashtags)
    branded = bv.branded_hashtags[0] if bv.branded_hashtags else "#LifeWithShamy"

    return f"""You are writing a social media caption for the Shamy brand
(two rescue cats: Amy fluffy Maine-Coon-style, Sheldon spotted Bengal-style).

Pillar: {pillar} — {pillar_obj.description}
Cat in this photo: {cat}

VOICE:
{bv.voice_primary}

DO:
{do_list}

DO NOT:
{dont_list}

FORBIDDEN TERMS (never use): {forbidden}

EXAMPLES for this pillar:
{example}

Task: Look at the photo. Produce EXACTLY 3 caption variants:
1. Short cat-POV (10-60 chars)
2. Medium cat-POV with a joke (60-180 chars)
3. Narrator-style (60-220 chars)

Then produce 5-8 hashtags. Always include {branded}.
Pillar-typical tags include: {pillar_tags}

Respond as STRICT JSON only — no preamble, no markdown fences:
{{
  "variants": ["...", "...", "..."],
  "hashtags": ["#...", "#..."]
}}
"""


def configure(api_key: str) -> None:
    global _client
    _client = genai.Client(api_key=api_key)


def generate(image_path: Path | str, bv: BrandVoice, pillar: str, cat: str) -> CaptionResult:
    if _client is None:
        raise RuntimeError("caption.configure(api_key) must be called first")
    prompt = build_prompt(bv, pillar, cat)
    img = Image.open(image_path)
    resp = _client.models.generate_content(model=MODEL_NAME, contents=[prompt, img])
    return _parse(resp.text or "")


def _parse(text: str) -> CaptionResult:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.DOTALL)
    data = json.loads(text)
    return CaptionResult(
        variants=[v.strip() for v in data.get("variants", [])],
        hashtags=[h.strip() for h in data.get("hashtags", [])],
    )


def validate_caption(res: CaptionResult, bv: BrandVoice) -> list[str]:
    issues: list[str] = []
    if len(res.variants) < 3:
        issues.append(f"Expected 3 variants, got {len(res.variants)}")
    if not (bv.hashtag_count_min <= len(res.hashtags) <= bv.hashtag_count_max):
        issues.append(
            f"Hashtag count {len(res.hashtags)} outside {bv.hashtag_count_min}-{bv.hashtag_count_max}"
        )
    branded_present = any(h in bv.branded_hashtags for h in res.hashtags)
    if not branded_present and bv.branded_hashtags:
        issues.append(f"Missing branded hashtag (need one of {bv.branded_hashtags})")
    joined = " ".join(res.variants).lower()
    for term in bv.forbidden_terms:
        if term.lower() in joined:
            issues.append(f"Forbidden term '{term}' found in caption")
    return issues
```

- [ ] **Step 4: Run tests, verify pass**

Run: `pytest tests/test_caption.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add pipeline/caption.py tests/test_caption.py
git commit -m "feat(caption): Gemini Vision caption + hashtag gen with brand-voice prompt"
```

---

## Task 11: `pipeline/telegram_bot.py` — approval card

**Files:**
- Create: `pipeline/telegram_bot.py`
- Create: `tests/test_telegram_smoke.py`

- [ ] **Step 1: Write implementation**

`pipeline/telegram_bot.py`:
```python
"""Telegram approval card — sends photo + caption variants, listens for button taps."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CallbackQueryHandler


@dataclass(frozen=True)
class ApprovalCard:
    slot_id: str
    platform: str
    pillar: str
    image_path: Path
    variants: list[str]
    hashtags: list[str]
    sound_url: str | None = None


def _format_caption(card: ApprovalCard) -> str:
    lines = [
        f"🐾 *{card.slot_id}* — `{card.platform}` · _{card.pillar}_",
        "",
        "*Variant 1 (short, cat-POV):*",
        card.variants[0] if card.variants else "(missing)",
        "",
        "*Variant 2 (medium, joke):*",
        card.variants[1] if len(card.variants) > 1 else "(missing)",
        "",
        "*Variant 3 (narrator):*",
        card.variants[2] if len(card.variants) > 2 else "(missing)",
        "",
        "*Hashtags:* " + " ".join(card.hashtags),
    ]
    if card.sound_url:
        lines += ["", f"🎵 [Suggested sound]({card.sound_url})"]
    return "\n".join(lines)


def _keyboard(slot_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve V1", callback_data=f"approve|{slot_id}|1"),
            InlineKeyboardButton("✅ V2",         callback_data=f"approve|{slot_id}|2"),
            InlineKeyboardButton("✅ V3",         callback_data=f"approve|{slot_id}|3"),
        ],
        [
            InlineKeyboardButton("✏️ Edit",  callback_data=f"edit|{slot_id}"),
            InlineKeyboardButton("⏭️ Skip",  callback_data=f"skip|{slot_id}"),
            InlineKeyboardButton("🚫 Block", callback_data=f"block|{slot_id}"),
        ],
    ])


async def send_approval(bot_token: str, chat_id: int, card: ApprovalCard) -> int:
    """Send an approval card. Returns the message_id for later editing."""
    app = Application.builder().token(bot_token).build()
    async with app:
        with card.image_path.open("rb") as fh:
            msg = await app.bot.send_photo(
                chat_id=chat_id,
                photo=InputFile(fh),
                caption=_format_caption(card),
                parse_mode="Markdown",
                reply_markup=_keyboard(card.slot_id),
            )
        return msg.message_id


def send_approval_sync(bot_token: str, chat_id: int, card: ApprovalCard) -> int:
    return asyncio.run(send_approval(bot_token, chat_id, card))
```

- [ ] **Step 2: Unit-test the formatter**

`tests/test_telegram_smoke.py`:
```python
from pathlib import Path
import os
import pytest

from pipeline.telegram_bot import ApprovalCard, _format_caption, send_approval_sync


def test_format_caption_renders_all_variants():
    card = ApprovalCard(
        slot_id="2026-07-07-ig",
        platform="instagram",
        pillar="cozy",
        image_path=Path("x.jpg"),
        variants=["A.", "B.", "C."],
        hashtags=["#LifeWithShamy", "#CatLoaf"],
    )
    txt = _format_caption(card)
    assert "Variant 1" in txt and "A." in txt
    assert "Variant 3" in txt and "C." in txt
    assert "#LifeWithShamy" in txt


def test_format_caption_with_sound_link():
    card = ApprovalCard(
        slot_id="s",
        platform="tiktok",
        pillar="cozy",
        image_path=Path("x.jpg"),
        variants=["A.", "B.", "C."],
        hashtags=["#a"],
        sound_url="https://tiktok.com/music/123",
    )
    txt = _format_caption(card)
    assert "Suggested sound" in txt
    assert "tiktok.com/music/123" in txt


@pytest.mark.skipif(
    not os.getenv("TELEGRAM_BOT_TOKEN") or not os.getenv("TELEGRAM_CHAT_ID_MEHUL"),
    reason="No Telegram token / chat id",
)
def test_smoke_send_to_mehul(tmp_path: Path):
    fixture = Path("tests/fixtures/amy_window.jpg")
    if not fixture.exists():
        pytest.skip("No fixture image")
    card = ApprovalCard(
        slot_id="smoke-test",
        platform="instagram",
        pillar="cozy",
        image_path=fixture,
        variants=["Smoke test.", "Smoke test medium.", "Smoke test narrator."],
        hashtags=["#LifeWithShamy", "#Test"],
    )
    msg_id = send_approval_sync(
        os.environ["TELEGRAM_BOT_TOKEN"],
        int(os.environ["TELEGRAM_CHAT_ID_MEHUL"]),
        card,
    )
    assert msg_id > 0
```

- [ ] **Step 3: Run unit tests, verify pass**

Run: `pytest tests/test_telegram_smoke.py -v -k "not smoke"`
Expected: 2 passed.

- [ ] **Step 4: Commit**

```bash
git add pipeline/telegram_bot.py tests/test_telegram_smoke.py
git commit -m "feat(telegram): approval card sender with inline keyboard"
```

---

## Task 12: `pipeline/run.py` — CLI entrypoint

**Files:**
- Create: `pipeline/run.py`

This wires Tasks 2–11 into one command: `python -m pipeline.run propose --date YYYY-MM-DD --platform PLATFORM`.

It handles approve/skip/block by waiting for an inline-button reply (polled). For v0.1 we keep it simple: the script proposes a single slot, sends the Telegram card, and **logs the proposed state** to `data/content-log.jsonl`. Sneha taps the button on her phone; the actual button-handler bot runs as a second process in Task 13.

- [ ] **Step 1: Write the CLI**

`pipeline/run.py`:
```python
"""CLI entrypoint: propose a single slot end-to-end."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from pipeline.brand import load_brand_voice
from pipeline.caption import configure as configure_caption, generate as generate_caption, validate_caption
from pipeline.config import load_settings
from pipeline.drive import authorize as drive_auth, download_file, list_folder_recursive
from pipeline.postlog import PostRecord, append_record, is_duplicate
from pipeline.privacy import configure as configure_privacy, check_image, is_safe_to_post
from pipeline.selector import DriveFile as SelectorFile, select_asset
from pipeline.slots import Platform, PostStatus, slot_from_dict
from pipeline.telegram_bot import ApprovalCard, send_approval_sync


CALENDAR_PATH = Path("data/content-calendar.json")
LOG_PATH = Path("data/content-log.jsonl")
TMP_DIR = Path("local/tmp")


def _cat_from_folder(folder: str) -> str:
    if folder.endswith("_amy"):
        return "Amy"
    if folder.endswith("_sheldon"):
        return "Sheldon"
    if folder.endswith("_both"):
        return "Amy and Sheldon"
    return "Amy and Sheldon"


def cmd_propose(args: argparse.Namespace) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    log = logging.getLogger("shamy.run")

    settings = load_settings()
    bv = load_brand_voice("data/brand-voice.yaml")

    calendar = json.loads(CALENDAR_PATH.read_text())
    target_date = date.fromisoformat(args.date)
    slot_dicts = [
        s for s in calendar["slots"]
        if date.fromisoformat(s["date"]) == target_date and s["platform"] == args.platform
    ]
    if not slot_dicts:
        log.error("No slot in calendar for %s / %s", args.date, args.platform)
        return 2
    slot = slot_from_dict(slot_dicts[0])
    log.info("Slot: %s pillar=%s", slot.id, slot.pillar)

    if is_duplicate(LOG_PATH, slot.id):
        log.warning("Slot %s already posted — skipping.", slot.id)
        return 0

    log.info("Authorising Drive…")
    svc = drive_auth()
    drive_files = list_folder_recursive(svc, settings.drive_root_folder_id)
    log.info("Drive: %d files across safe folders", len(drive_files))

    used = {r.asset_path for r in __import__("pipeline.postlog", fromlist=["load_all"]).load_all(LOG_PATH)}
    selector_files = [
        SelectorFile(id=f.id, name=f.name, folder=f.folder, mime_type=f.mime_type)
        for f in drive_files
    ]
    pick = select_asset(selector_files, pillar=slot.pillar, used_ids=used)
    if not pick:
        log.error("No asset matches pillar=%s. Send Sneha a nudge.", slot.pillar)
        return 3

    log.info("Picked: %s/%s", pick.folder, pick.name)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    local_path = download_file(svc, pick.id, TMP_DIR / pick.name)

    configure_privacy(settings.gemini_api_key)
    verdict = check_image(local_path)
    log.info("Privacy: %s (conf=%.2f)", "BLOCK" if verdict.has_human else "OK", verdict.confidence)
    if not is_safe_to_post(verdict):
        log.error("Privacy check blocked: %s", verdict.reason)
        return 4

    configure_caption(settings.gemini_api_key)
    cat = _cat_from_folder(pick.folder)
    cap = generate_caption(local_path, bv, slot.pillar, cat)
    issues = validate_caption(cap, bv)
    if issues:
        log.warning("Caption issues: %s", "; ".join(issues))

    card = ApprovalCard(
        slot_id=slot.id,
        platform=slot.platform.value,
        pillar=slot.pillar,
        image_path=local_path,
        variants=cap.variants,
        hashtags=cap.hashtags,
        sound_url=None,
    )

    for chat_id in (settings.telegram_chat_id_sneha, settings.telegram_chat_id_mehul):
        send_approval_sync(settings.telegram_bot_token, chat_id, card)
    log.info("Approval card sent.")

    record = PostRecord(
        slot_id=slot.id,
        platform=slot.platform.value,
        pillar=slot.pillar,
        asset_path=f"{pick.folder}/{pick.name}",
        caption="(proposed)",
        hashtags=cap.hashtags,
        timestamp_utc=datetime.now(timezone.utc),
        sound_url=None,
        external_post_id=None,
    )
    append_record(LOG_PATH, record)
    log.info("Recorded proposal in %s", LOG_PATH)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser("shamy")
    sub = p.add_subparsers(dest="command", required=True)
    pr = sub.add_parser("propose", help="Propose a single slot")
    pr.add_argument("--date", required=True, help="YYYY-MM-DD")
    pr.add_argument("--platform", required=True, choices=[x.value for x in Platform])
    pr.set_defaults(func=cmd_propose)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Smoke-test help output**

Run: `python -m pipeline.run propose --help`
Expected: argparse help text appears, exits 0.

- [ ] **Step 3: Commit**

```bash
git add pipeline/run.py
git commit -m "feat(run): CLI entrypoint wiring slot→drive→privacy→caption→telegram"
```

---

## Task 13: Button-handler bot (`pipeline/approval_listener.py`)

**Files:**
- Create: `pipeline/approval_listener.py`

A long-running second process (run on Mehul's laptop or a free Render worker) that listens for inline-button taps on Telegram approval cards and reacts:
- `approve|<slot_id>|<variant_num>` → mark APPROVED in log; for v0.1, this just confirms — actual publishing is **manual** by Mehul via Vizard web UI using the selected variant text.
- `edit|<slot_id>` → bot replies: "Send me the new caption as a reply to this message." Captures next message as override caption.
- `skip|<slot_id>` → mark SKIPPED in log; do nothing else.
- `block|<slot_id>` → mark BLOCKED, request that the asset be moved to `02_humans_in_frame/`.

- [ ] **Step 1: Write the listener**

`pipeline/approval_listener.py`:
```python
"""Long-running Telegram listener that updates the post log on button taps."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes, MessageHandler, filters

from pipeline.config import load_settings
from pipeline.postlog import PostRecord, append_record, load_all

LOG_PATH = Path("data/content-log.jsonl")
APPROVALS_PATH = Path("data/approvals.jsonl")

log = logging.getLogger("shamy.listener")


def _record_decision(slot_id: str, decision: str, variant: int | None = None) -> None:
    APPROVALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "slot_id": slot_id,
        "decision": decision,
        "variant": variant,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    with APPROVALS_PATH.open("a") as f:
        f.write(json.dumps(entry) + "\n")


async def on_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    if not q or not q.data:
        return
    await q.answer()
    parts = q.data.split("|")
    action = parts[0]
    slot_id = parts[1] if len(parts) > 1 else "?"
    variant = int(parts[2]) if len(parts) > 2 else None

    if action == "approve":
        _record_decision(slot_id, "approved", variant)
        await q.edit_message_caption(caption=f"✅ Approved (V{variant}) — {slot_id}\n\nNow publish via Vizard.")
    elif action == "skip":
        _record_decision(slot_id, "skipped")
        await q.edit_message_caption(caption=f"⏭️ Skipped — {slot_id}")
    elif action == "block":
        _record_decision(slot_id, "blocked")
        await q.edit_message_caption(
            caption=f"🚫 Blocked — {slot_id}\n\nPlease move this asset to 02_humans_in_frame/ in Drive."
        )
    elif action == "edit":
        _record_decision(slot_id, "edit_requested")
        await q.edit_message_caption(
            caption=f"✏️ Edit requested for {slot_id}.\nReply to this message with the new caption."
        )


async def main_async() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    settings = load_settings()
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CallbackQueryHandler(on_button))
    log.info("Listener up. Waiting for button taps…")
    await app.run_polling(close_loop=False)


if __name__ == "__main__":
    asyncio.run(main_async())
```

- [ ] **Step 2: Smoke test (manual)**

Run in one terminal:
```bash
python -m pipeline.approval_listener
```
In another terminal, run the propose flow against a real photo:
```bash
python -m pipeline.run propose --date 2026-07-07 --platform instagram
```
Tap a button in Telegram on your phone.
Expected: the caption updates in place, an entry appears in `data/approvals.jsonl`.

- [ ] **Step 3: Commit**

```bash
git add pipeline/approval_listener.py
git commit -m "feat(listener): Telegram button handler updating approvals log"
```

---

## Task 14: Operational docs (runbook + sister-handoff)

**Files:**
- Create: `docs/runbook.md`
- Create: `docs/sister-handoff.md`

- [ ] **Step 1: Write the runbook**

`docs/runbook.md`:
```markdown
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
```

- [ ] **Step 2: Write Sneha's handoff**

`docs/sister-handoff.md`:
```markdown
# Hi Sneha — How Shamy posts work

Mehul set up an automation for Amy & Sheldon. Here's all you need to know.

## 1) Put photos into the right folders in Google Drive

Open the `Shamy Content` folder Mehul shared with you. You'll see:

- `00_inbox/` — drop everything here first.
- `01_safe_amy/` — Amy only, no you or Anish in frame.
- `01_safe_sheldon/` — Sheldon only, no you or Anish.
- `01_safe_both/` — both cats, no humans.
- `02_humans_in_frame/` — anything that has you or Anish in it. We never post from this folder.
- `03_videos_raw/` — videos (the long ones too).

**The rule that matters most:** if you or Anish are anywhere in the photo (even a hand, even a foot, even a reflection), it goes in `02_humans_in_frame/`. The system also double-checks, but the folder is the most important boundary.

**Naming hint (optional):** if you can rename files like `amy_cozy_001.jpg` or `sheldon_snack_005.jpg`, the bot picks the right photo for the right "mood." If you don't have time, no problem — just sort into folders and Mehul will tag.

## 2) Approve posts on Telegram

You'll get messages from the **Shamy bot** on Telegram. Each looks like a photo with three caption options. Just tap one of these:

- ✅ **Approve V1/V2/V3** — picks that caption. Done.
- ✏️ **Edit** — bot will ask you to type a new caption.
- ⏭️ **Skip** — not this one, pick a different photo.
- 🚫 **Block** — there's a human in this photo, please remove it from the safe folder.

You can do this from anywhere — couch, bus, in line at Edeka. Takes 10 seconds.

## 3) For TikTok only — one extra tap

For TikTok posts (3 per week), Mehul will DM you:
- The ready video
- A link to a trending sound
Open TikTok → tap the sound link → upload the video → post. Total: 30 seconds.

That's it! Questions: ping Mehul.
```

- [ ] **Step 3: Commit**

```bash
git add docs/runbook.md docs/sister-handoff.md
git commit -m "docs: runbook for Mehul + Sneha handoff guide"
```

---

## Task 15: End-to-end dry run

- [ ] **Step 1: Create a dry-run flag in run.py and exercise the full path**

Add a `--dry-run` flag (`if settings.dry_run` already passed via env). When set: don't actually send Telegram, just print the card payload.

Modify the bottom of `cmd_propose`:
```python
    if settings.dry_run:
        log.info("DRY RUN — skipping Telegram send")
        log.info("Card payload: slot=%s pillar=%s variants=%s hashtags=%s",
                 card.slot_id, card.pillar, card.variants, card.hashtags)
    else:
        for chat_id in (settings.telegram_chat_id_sneha, settings.telegram_chat_id_mehul):
            send_approval_sync(settings.telegram_bot_token, chat_id, card)
        log.info("Approval card sent.")
```

- [ ] **Step 2: Run an end-to-end dry run**

Place one test photo in Drive `01_safe_amy/amy_cozy_test_001.jpg`.

Run:
```bash
DRY_RUN=true python -m pipeline.run propose --date 2026-07-07 --platform instagram
```

Expected output (rough):
```
INFO Slot: 2026-07-07-ig pillar=snack_reactions
INFO Authorising Drive…
INFO Drive: N files across safe folders
INFO Picked: 01_safe_amy/amy_cozy_test_001.jpg
INFO Privacy: OK (conf=0.95)
INFO DRY RUN — skipping Telegram send
INFO Recorded proposal in data/content-log.jsonl
```

- [ ] **Step 3: Verify content log has the entry**

Run: `tail -1 data/content-log.jsonl | python -m json.tool`
Expected: well-formed JSON record with `slot_id`, `pillar`, `hashtags`, `timestamp_utc`.

- [ ] **Step 4: Commit**

```bash
git add pipeline/run.py
git commit -m "feat(run): dry-run mode for end-to-end verification without Telegram"
```

---

## Task 16: GitHub Actions skeleton (cron-ready, off by default)

**Files:**
- Create: `.github/workflows/daily-propose.yml`

- [ ] **Step 1: Write workflow**

`.github/workflows/daily-propose.yml`:
```yaml
name: Daily propose

on:
  schedule:
    - cron: "0 6 * * *"   # 06:00 UTC = 08:00 CET (or 07:00 in winter)
  workflow_dispatch:
    inputs:
      date:
        description: "Override target date YYYY-MM-DD"
        required: false
      platform:
        description: "Platform (instagram|x|tiktok)"
        required: true
        default: instagram

jobs:
  propose:
    runs-on: ubuntu-latest
    if: vars.PIPELINE_ENABLED == 'true'   # set this var to 'true' in repo settings to enable
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - name: Restore drive token
        run: |
          echo '${{ secrets.GOOGLE_TOKEN_JSON }}' > token.json
          echo '${{ secrets.GOOGLE_CREDENTIALS_JSON }}' > credentials.json
      - name: Propose
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID_SNEHA: ${{ secrets.TELEGRAM_CHAT_ID_SNEHA }}
          TELEGRAM_CHAT_ID_MEHUL: ${{ secrets.TELEGRAM_CHAT_ID_MEHUL }}
          DRIVE_ROOT_FOLDER_ID: ${{ secrets.DRIVE_ROOT_FOLDER_ID }}
          TZ: Europe/Berlin
        run: |
          PLATFORM="${{ inputs.platform || 'instagram' }}"
          DATE="${{ inputs.date || '$(date +%Y-%m-%d)' }}"
          python -m pipeline.run propose --date "$DATE" --platform "$PLATFORM"
      - name: Commit log changes
        run: |
          git config user.name "shamy-bot"
          git config user.email "shamy-bot@users.noreply.github.com"
          git add data/content-log.jsonl
          git diff --cached --quiet || git commit -m "chore: record proposed post"
          git push
```

- [ ] **Step 2: Verify YAML parses**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/daily-propose.yml')); print('ok')"`
Expected: `ok`.

- [ ] **Step 3: Commit (do NOT enable the var yet)**

```bash
git add .github/workflows/daily-propose.yml
git commit -m "feat(ci): daily propose workflow, gated behind PIPELINE_ENABLED var"
```

- [ ] **Step 4: Document the enable step in runbook**

Append to `docs/runbook.md`:
```markdown
## Enabling the cron
1. In GitHub repo settings → Actions → Variables → New repository variable: `PIPELINE_ENABLED = true`.
2. In Secrets → add all the keys (GEMINI, TELEGRAM, DRIVE).
3. After one week of supervised runs in `workflow_dispatch` mode, flip the var to `true` to start the cron.
```

Run: `git add docs/runbook.md && git commit -m "docs: cron enable instructions"`

---

## Self-review checklist (run after all tasks)

- [ ] Spec section §5 cadence: calendar in Task 5 matches (IG 4/wk, X mirrors, TikTok 3/wk). ✅
- [ ] Spec §7 privacy two-layer: folder boundary (selector excludes humans folder) + Gemini Vision check. ✅
- [ ] Spec §8 stack: Gemini, GitHub Actions, Telegram, Drive, ffmpeg-deferred-to-v0.3, Vizard manual in v0.1. ✅
- [ ] Spec §10 data flow: matches Tasks 7→8→9→10→11→12→13. ✅
- [ ] Spec §14 MVP: 50 photo seed (Sneha task), repo skeleton ✅, caption_gen ✅, privacy ✅, Telegram bot ✅, manual publish (Mehul Vizard web UI) ✅, TikTok handoff ✅.
- [ ] No placeholders: every task has full code, no "TBD". ✅
- [ ] Type consistency: `DriveFile` exists in both `pipeline.drive` and `pipeline.selector`. Note: they're intentionally separate dataclasses to keep `selector` testable without google deps; `run.py` converts between them. ✅

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-29-shamy-pipeline-v0.1.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
