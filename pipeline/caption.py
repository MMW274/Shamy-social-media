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
