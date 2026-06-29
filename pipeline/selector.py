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
