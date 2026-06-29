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
