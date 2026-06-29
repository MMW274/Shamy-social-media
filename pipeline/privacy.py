"""Privacy check: does this image/video frame contain a human?

Layer 2 of two-layer privacy defense (layer 1 = Drive folder boundary).
Uses the new google-genai SDK (the legacy google-generativeai is EOL).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from google import genai
from PIL import Image


PROMPT = (
    "You are a privacy gatekeeper for a cat-content social media account. "
    "Examine this image. Is there ANY identifiable human element visible — "
    "a face, body part (hand, arm, leg, foot), or clearly human silhouette? "
    "Reflections, blurred humans, or partial humans also count.\n\n"
    "Respond in this exact format on a single line:\n"
    "VERDICT=<YES|NO|UNSURE> CONFIDENCE=<0.0-1.0> REASON=<short reason>"
)

MODEL_NAME = "gemini-2.5-flash"

# Module-level client, initialised by `configure()`.
_client: genai.Client | None = None


@dataclass(frozen=True)
class PrivacyVerdict:
    has_human: bool
    confidence: float
    reason: str
    raw: str


def configure(api_key: str) -> None:
    global _client
    _client = genai.Client(api_key=api_key)


def check_image(path: Path | str) -> PrivacyVerdict:
    if _client is None:
        raise RuntimeError("privacy.configure(api_key) must be called first")
    img = Image.open(path)
    resp = _client.models.generate_content(model=MODEL_NAME, contents=[PROMPT, img])
    text = (resp.text or "").strip()
    return _parse_verdict(text)


def _parse_verdict(text: str) -> PrivacyVerdict:
    verdict_str, conf, reason = "UNSURE", 0.0, text
    for token in text.replace("\n", " ").split():
        if token.startswith("VERDICT="):
            verdict_str = token.split("=", 1)[1].upper().strip(",")
        elif token.startswith("CONFIDENCE="):
            try:
                conf = float(token.split("=", 1)[1].strip(","))
            except ValueError:
                conf = 0.0
    if "REASON=" in text:
        reason = text.split("REASON=", 1)[1].strip()

    has_human = verdict_str == "YES" or (verdict_str == "UNSURE" and conf > 0.4)
    return PrivacyVerdict(has_human=has_human, confidence=conf, reason=reason, raw=text)


def is_safe_to_post(verdict: PrivacyVerdict, min_no_confidence: float = 0.7) -> bool:
    """Returns True only when the model says NO with high confidence."""
    if verdict.has_human:
        return False
    return verdict.confidence >= min_no_confidence
