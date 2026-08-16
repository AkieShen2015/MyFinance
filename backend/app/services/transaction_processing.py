import re
from dataclasses import dataclass

REFERENCE_PATTERN = re.compile(r"\b(?:REF|CARD|POS)?\s*\d{4,}\b", re.IGNORECASE)
WHITESPACE_PATTERN = re.compile(r"\s+")


@dataclass(frozen=True)
class NormalisedDescription:
    original: str
    value: str


def normalise_description(description: str) -> NormalisedDescription:
    """Produce a stable matching value while preserving the provider description."""
    value = description.upper().strip()
    value = REFERENCE_PATTERN.sub(" ", value)
    value = re.sub(r"[^A-Z0-9&.'/-]+", " ", value)
    value = WHITESPACE_PATTERN.sub(" ", value).strip(" -/")
    return NormalisedDescription(original=description, value=value)
