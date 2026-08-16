from app.services.transaction_processing import normalise_description


def test_description_normalisation_is_deterministic_and_preserves_original() -> None:
    result = normalise_description("  Woolworths 1234 Sydney  REF 987654  ")

    assert result.original == "  Woolworths 1234 Sydney  REF 987654  "
    assert result.value == "WOOLWORTHS SYDNEY"


def test_description_normalisation_keeps_meaningful_punctuation() -> None:
    assert normalise_description("O'Brien & Co. / Cafe").value == "O'BRIEN & CO. / CAFE"
