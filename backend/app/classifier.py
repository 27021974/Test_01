"""Rule-based insolvency keyword classifier for German texts."""
from __future__ import annotations

import re

# Ordered by importance – more specific patterns score higher
INSOLVENCY_KEYWORDS: list[tuple[str, float]] = [
    (r"\binsolvenzbekanntmachung\b", 1.0),
    (r"\binsolvenzverfahren\s+er[öo]ffn", 1.0),
    (r"\binsolvenzantrag\b", 0.9),
    (r"\binsolvenz\b", 0.8),
    (r"\bzahlungsunf[äa]hig\b", 0.9),
    (r"\b[üu]berschuldung\b", 0.7),
    (r"\bvorl[äa]ufig(er)?\s+insolvenzverwalter\b", 1.0),
    (r"\binsolvenzverwalter\b", 0.9),
    (r"\brestrukturierung\b", 0.4),
    (r"\bvergleichsverfahren\b", 0.6),
    (r"\bmasseunzul[äa]nglichkeit\b", 1.0),
    (r"\bgl[äa]ubigerversammlung\b", 0.6),
    (r"\babwicklung\b", 0.3),
    (r"\bliquidation\b", 0.4),
    (r"\bkonkurs\b", 0.8),
    (r"\bverfahren\s+eingestellt\b", 0.5),
]

# Pre-compile all patterns (case-insensitive)
_COMPILED: list[tuple[re.Pattern, float]] = [
    (re.compile(pat, re.IGNORECASE), score) for pat, score in INSOLVENCY_KEYWORDS
]


def compute_insolvency_score(text: str) -> float:
    """Return a score in [0, 1] reflecting how likely the text concerns insolvency.

    The score is the maximum of all matching keyword weights rather than a sum
    so that repeated mentions don't inflate it beyond 1.0.
    """
    if not text:
        return 0.0
    max_score = 0.0
    for pattern, weight in _COMPILED:
        if pattern.search(text):
            max_score = max(max_score, weight)
    return round(max_score, 4)


def is_insolvency_event(score: float, threshold: float = 0.5) -> bool:
    """Return True if score is at or above threshold."""
    return score >= threshold
