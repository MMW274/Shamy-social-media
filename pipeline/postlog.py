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
