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
