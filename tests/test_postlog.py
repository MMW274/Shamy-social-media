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
