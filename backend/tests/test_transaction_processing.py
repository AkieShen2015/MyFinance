from app.services.transaction_processing import normalise_description, normalise_merchant


def test_description_normalisation_is_deterministic_and_preserves_original() -> None:
    result = normalise_description("  Woolworths 1234 Sydney  REF 987654  ")

    assert result.original == "  Woolworths 1234 Sydney  REF 987654  "
    assert result.value == "WOOLWORTHS SYDNEY"


def test_description_normalisation_keeps_meaningful_punctuation() -> None:
    assert normalise_description("O'Brien & Co. / Cafe").value == "O'BRIEN & CO. / CAFE"


def test_known_local_merchant_aliases_share_stable_identities() -> None:
    assert normalise_merchant("ZLBEL PTY LTD Weston").canonical_name == "zlbel"
    assert normalise_merchant("SQ *KWAFOOD 1982 Canberra").canonical_name == "kwafood-1982"
    assert normalise_merchant("YIJIA ASIAN GROCERY").display_name == "Yijia Asian Grocery"
    assert normalise_merchant("Canberra Cat Vet Belconnen 035").merchant_type == "vet"


def test_unknown_merchant_removes_payment_and_legal_noise() -> None:
    merchant = normalise_merchant("SQ *Example Foods Pty Ltd Canberra 123456")

    assert merchant.canonical_name == "example-foods"
    assert merchant.display_name == "Example Foods"
