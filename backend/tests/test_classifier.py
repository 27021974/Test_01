"""Unit tests for the insolvency keyword classifier."""
import pytest

from app.classifier import compute_insolvency_score, is_insolvency_event


@pytest.mark.parametrize(
    "text,expected_min",
    [
        ("Insolvenzbekanntmachung über das Vermögen der Muster GmbH", 1.0),
        ("Insolvenzverfahren eröffnet über das Vermögen", 1.0),
        ("Insolvenzantrag gestellt", 0.9),
        ("Insolvenz der Firma Schmidt", 0.8),
        ("zahlungsunfähig erklärt", 0.9),
        ("Insolvenzverwalter bestellt", 0.9),
        ("Vorläufiger Insolvenzverwalter eingesetzt", 1.0),
        ("Masseunzulänglichkeit angezeigt", 1.0),
        ("Gläubigerversammlung einberufen", 0.6),
        ("Neue Produkte auf dem Markt", 0.0),
        ("Jahresabschluss veröffentlicht", 0.0),
        ("", 0.0),
    ],
)
def test_insolvency_score(text: str, expected_min: float) -> None:
    score = compute_insolvency_score(text)
    assert score >= expected_min, f"Expected score >= {expected_min} for: {text!r}, got {score}"
    assert 0.0 <= score <= 1.0


def test_score_case_insensitive() -> None:
    assert compute_insolvency_score("INSOLVENZ") == compute_insolvency_score("insolvenz")


def test_is_insolvency_event_threshold() -> None:
    assert is_insolvency_event(0.8) is True
    assert is_insolvency_event(0.5) is True
    assert is_insolvency_event(0.49) is False
    assert is_insolvency_event(0.0) is False


def test_non_insolvency_text_returns_zero() -> None:
    assert compute_insolvency_score("Handelsregistereintrag Neueintragung") == 0.0
