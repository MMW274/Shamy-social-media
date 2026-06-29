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
