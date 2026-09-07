"""Rule-based enrichment for German insolvency market intelligence."""
from __future__ import annotations

import re


LEGAL_FORM_PATTERNS: list[tuple[str, str]] = [
    (r"\bGmbH\s*&\s*Co\.\s*KG\b", "GmbH & Co. KG"),
    (r"\bUG\s*\(haftungsbeschr[äa]nkt\)\b", "UG (haftungsbeschränkt)"),
    (r"\bGmbH\b", "GmbH"),
    (r"\bAG\b", "AG"),
    (r"\bKG\b", "KG"),
    (r"\bOHG\b", "OHG"),
    (r"\be\.?\s*K\.?\b", "e.K."),
]

PROCEDURE_PATTERNS: list[tuple[str, str]] = [
    (r"vorl[äa]ufig(?:e[rsn])?\s+insolvenz", "Vorläufiges Verfahren"),
    (r"insolvenzverfahren\s+er[öo]ffn", "Eröffnetes Verfahren"),
    (r"mangels\s+masse|mangels\s+einer\s+die\s+kosten", "Abweisung mangels Masse"),
    (r"eigenverwaltung", "Eigenverwaltung"),
    (r"schutzschirm", "Schutzschirmverfahren"),
    (r"masseunzul[äa]nglichkeit", "Masseunzulänglichkeit"),
    (r"verfahren\s+eingestellt|aufgehoben", "Aufhebung/Einstellung"),
]

INDUSTRY_KEYWORDS: list[tuple[str, str, str]] = [
    (r"\bbau|hochbau|tiefbau|immobilien|projektentwicklung", "Bau & Immobilien", "F"),
    (r"\bhandel|einzelhandel|gro[ßs]handel|e-commerce|shop", "Handel", "G"),
    (r"\bgastro|restaurant|hotel|catering|tourismus", "Gastgewerbe", "I"),
    (r"\blogistik|transport|spedition|kurier", "Logistik & Transport", "H"),
    (r"\bmaschinenbau|produktion|fertigung|industrie", "Industrie & Produktion", "C"),
    (r"\bit|software|digital|agentur|beratung", "IT & Dienstleistungen", "J/M"),
    (r"\bpflege|medizin|klinik|gesundheit", "Gesundheit & Soziales", "Q"),
    (r"\benergie|solar|photovoltaik|wind", "Energie", "D"),
]

COURT_PATTERN = re.compile(r"\b(?:Amtsgericht|AG)\s+([A-ZÄÖÜ][A-Za-zÄÖÜäöüß\-\s]+)", re.IGNORECASE)
CASE_PATTERN = re.compile(r"\b(?:Az\.?|Aktenzeichen)\s*:?\s*([0-9A-Za-z\s./-]{3,40})", re.IGNORECASE)
POSTAL_CITY_PATTERN = re.compile(r"\b(\d{5})\s+([A-ZÄÖÜ][A-Za-zÄÖÜäöüß\-\s]+)")
COMPANY_PATTERNS = [
    re.compile(r"über\s+das\s+Vermögen\s+der\s+(.+?)(?:,|\sin\s|\smit\s|$)", re.IGNORECASE),
    re.compile(r"über\s+das\s+Vermögen\s+des\s+(.+?)(?:,|\sin\s|\smit\s|$)", re.IGNORECASE),
    re.compile(r"Schuldner(?:in)?\s*:?\s*(.+?)(?:,|\n|$)", re.IGNORECASE),
]

CITY_TO_STATE = {
    "Berlin": "Berlin",
    "Hamburg": "Hamburg",
    "München": "Bayern",
    "Munich": "Bayern",
    "Nürnberg": "Bayern",
    "Stuttgart": "Baden-Württemberg",
    "Karlsruhe": "Baden-Württemberg",
    "Frankfurt": "Hessen",
    "Wiesbaden": "Hessen",
    "Köln": "Nordrhein-Westfalen",
    "Düsseldorf": "Nordrhein-Westfalen",
    "Dortmund": "Nordrhein-Westfalen",
    "Essen": "Nordrhein-Westfalen",
    "Bremen": "Bremen",
    "Hannover": "Niedersachsen",
    "Leipzig": "Sachsen",
    "Dresden": "Sachsen",
    "Potsdam": "Brandenburg",
    "Rostock": "Mecklenburg-Vorpommern",
    "Kiel": "Schleswig-Holstein",
    "Mainz": "Rheinland-Pfalz",
    "Saarbrücken": "Saarland",
    "Erfurt": "Thüringen",
    "Magdeburg": "Sachsen-Anhalt",
}


def infer_legal_form(text: str) -> str | None:
    for pattern, legal_form in LEGAL_FORM_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return legal_form
    return None


def infer_company_name(text: str) -> str | None:
    for pattern in COMPANY_PATTERNS:
        match = pattern.search(text)
        if match:
            name = re.sub(r"\s+", " ", match.group(1)).strip(" .;:-")
            if 3 <= len(name) <= 255:
                return name
    return None


def infer_procedure_type(text: str) -> str:
    for pattern, procedure_type in PROCEDURE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return procedure_type
    return "Insolvenzbekanntmachung"


def infer_industry(text: str) -> tuple[str | None, str | None]:
    for pattern, industry, code in INDUSTRY_KEYWORDS:
        if re.search(pattern, text, re.IGNORECASE):
            return industry, code
    return None, None


def extract_court(text: str) -> str | None:
    match = COURT_PATTERN.search(text)
    if not match:
        return None
    return f"Amtsgericht {match.group(1).strip()}"


def extract_case_number(text: str) -> str | None:
    match = CASE_PATTERN.search(text)
    return match.group(1).strip(" .;,\n\t") if match else None


def extract_postal_city(text: str) -> tuple[str | None, str | None]:
    match = POSTAL_CITY_PATTERN.search(text)
    if not match:
        return None, None
    return match.group(1), match.group(2).strip()


def infer_bundesland(city: str | None, court: str | None = None) -> str | None:
    candidates = [city, court.replace("Amtsgericht ", "") if court else None]
    for candidate in candidates:
        if not candidate:
            continue
        normalized = candidate.strip()
        for city_name, state in CITY_TO_STATE.items():
            if city_name.lower() in normalized.lower():
                return state
    return None
