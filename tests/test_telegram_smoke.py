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
