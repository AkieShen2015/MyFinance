from __future__ import annotations

import re
from dataclasses import dataclass

REFERENCE_PATTERN = re.compile(r"\b(?:REF|CARD|POS)?\s*\d{4,}\b", re.IGNORECASE)
WHITESPACE_PATTERN = re.compile(r"\s+")
PAYMENT_PREFIX_PATTERN = re.compile(
    r"^(?:CARD PURCHASE|DEBIT PURCHASE|EFTPOS|PAYPAL\s*\*?|SQ\s*\*?|SQUARE\s*\*?)\s*",
    re.IGNORECASE,
)
LEGAL_SUFFIX_PATTERN = re.compile(
    r"\b(?:PTY\.?\s+LTD\.?|PROPRIETARY\s+LIMITED|LIMITED|LTD\.?)\b.*$",
    re.IGNORECASE,
)
MERCHANT_ALIASES: tuple[tuple[re.Pattern[str], str, str, str | None], ...] = (
    (
        re.compile(r"\bZLBEL(?:\s+PTY\s+LTD)?\b", re.IGNORECASE),
        "zlbel",
        "ZhangLiang Malatang",
        "restaurant",
    ),
    (
        re.compile(r"\bKWAFOOD(?:\s*1982)?\b", re.IGNORECASE),
        "kwafood-1982",
        "Kwafood 1982",
        "restaurant",
    ),
    (
        re.compile(r"\bYIJIA\s+ASIAN\s+GROCERY\b", re.IGNORECASE),
        "yijia-asian-grocery",
        "Yijia Asian Grocery",
        "supermarket",
    ),
    (
        re.compile(r"\bCANBERRA\s+CAT\s+VET\b", re.IGNORECASE),
        "canberra-cat-vet",
        "Canberra Cat Vet",
        "vet",
    ),
)


@dataclass(frozen=True)
class NormalisedDescription:
    original: str
    value: str


@dataclass(frozen=True)
class NormalisedMerchant:
    canonical_name: str
    display_name: str
    merchant_type: str | None = None


def normalise_description(description: str) -> NormalisedDescription:
    """Produce a stable matching value while preserving the provider description."""
    value = description.upper().strip()
    value = REFERENCE_PATTERN.sub(" ", value)
    value = re.sub(r"[^A-Z0-9&.'/-]+", " ", value)
    value = WHITESPACE_PATTERN.sub(" ", value).strip(" -/")
    return NormalisedDescription(original=description, value=value)


def normalise_merchant(description: str) -> NormalisedMerchant:
    """Return a stable merchant identity without exposing the original provider payload."""
    normalised = normalise_description(description).value
    for pattern, canonical_name, display_name, merchant_type in MERCHANT_ALIASES:
        if pattern.search(normalised):
            return NormalisedMerchant(canonical_name, display_name, merchant_type)

    merchant_name = PAYMENT_PREFIX_PATTERN.sub("", normalised)
    merchant_name = LEGAL_SUFFIX_PATTERN.sub("", merchant_name)
    merchant_name = re.sub(r"\b\d{3,}\b", " ", merchant_name)
    merchant_name = WHITESPACE_PATTERN.sub(" ", merchant_name).strip(" -/.*")
    if not merchant_name:
        merchant_name = normalised or "Unknown merchant"
    canonical_name = re.sub(r"[^a-z0-9]+", "-", merchant_name.casefold()).strip("-")
    return NormalisedMerchant(canonical_name or "unknown-merchant", merchant_name.title())
