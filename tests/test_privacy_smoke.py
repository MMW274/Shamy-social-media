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
    assert v.raw
