"""Loads and validates data/brand-voice.yaml into a typed config."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class CatProfile:
    aka: list[str]
    look: str
    personality: list[str]
    voice_traits: list[str]
    catchphrases: list[str]


@dataclass(frozen=True)
class Pillar:
    description: str
    example_captions: list[str]
    typical_hashtags: list[str]
    voice_override: str | None = None


@dataclass(frozen=True)
class BrandVoice:
    brand_name: str
    tagline: str
    cats: dict[str, CatProfile]
    voice_primary: str
    voice_do: list[str]
    voice_do_not: list[str]
    forbidden_terms: list[str]
    pillars: dict[str, Pillar]
    branded_hashtags: list[str]
    hashtag_count_min: int
    hashtag_count_max: int
    raw: dict = field(default_factory=dict)


def load_brand_voice(path: Path | str) -> BrandVoice:
    data = yaml.safe_load(Path(path).read_text())

    cats = {}
    for key, name in (("amy", "Amy"), ("sheldon", "Sheldon")):
        c = data["cats"][key]
        cats[name] = CatProfile(
            aka=c.get("aka", []),
            look=c.get("look", ""),
            personality=c.get("personality", []),
            voice_traits=c.get("voice_traits", []),
            catchphrases=c.get("catchphrases", []),
        )

    pillars = {
        name: Pillar(
            description=p.get("description", ""),
            example_captions=p.get("example_captions", []),
            typical_hashtags=p.get("typical_hashtags", []),
            voice_override=p.get("voice_override"),
        )
        for name, p in data.get("pillars", {}).items()
    }

    rules = data.get("caption_generation_rules", {})
    hc = rules.get("hashtag_count", [5, 8])

    return BrandVoice(
        brand_name=data["brand"]["name"],
        tagline=data["brand"].get("tagline", ""),
        cats=cats,
        voice_primary=data["voice"]["primary"],
        voice_do=data["voice"].get("do", []),
        voice_do_not=data["voice"].get("do_not", []),
        forbidden_terms=data.get("privacy", {}).get("forbidden_terms_in_captions", []),
        pillars=pillars,
        branded_hashtags=data.get("hashtag_bank", {}).get("branded_always_include_one", []),
        hashtag_count_min=int(hc[0]),
        hashtag_count_max=int(hc[1]),
        raw=data,
    )
