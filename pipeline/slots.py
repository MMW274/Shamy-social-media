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
