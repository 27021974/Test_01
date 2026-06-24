# Marktbeobachtungs-WebApp – Insolvenz-Monitor

MVP-WebApp zur Beobachtung von Insolvenzbekanntmachungen und KMU-relevanten Marktereignissen.

---

## Architekturüberblick

```
┌─────────────────────────────────────────────────────────┐
│                     Docker Compose                       │
│                                                         │
│  ┌──────────────────────┐   ┌─────────────────────────┐│
│  │   Frontend           │   │   Backend (FastAPI)      ││
│  │   React + Vite       │──▶│   + APScheduler          ││
│  │   Port 3000          │   │   Port 8000              ││
│  └──────────────────────┘   └──────────┬────────────────┘│
│                                        │                 │
│                              ┌─────────▼──────────────┐ │
│                              │  SQLite (SQLAlchemy)    │ │
│                              │  /app/data/*.db         │ │
│                              └────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Komponenten

| Schicht | Technologie | Beschreibung |
|---------|-------------|--------------|
| Backend | Python 3.12 + FastAPI | REST-API, Scheduler, Ingestion-Pipeline |
| Frontend | React 19 + Vite | Dashboard, Filteransicht, Detailseite |
| Datenbank | SQLite (via SQLAlchemy async) | MVP – einfach auf Postgres umstellbar |
| Scheduler | APScheduler | Täglicher Fetch-Job (konfigurierbar) |
| Container | Docker + docker-compose | Ein-Befehl-Start |

---

## Setup & Start

### Option A: Docker (empfohlen)

```bash
# 1. Konfiguration anlegen
cp .env.example .env
# Ggf. API_TOKEN in .env anpassen

# 2. Starten
docker compose up --build

# → Frontend: http://localhost:3000
# → Backend API: http://localhost:8000
# → Swagger UI: http://localhost:8000/docs
```

### Option B: Lokal (ohne Docker)

**Backend:**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env

uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## Implementierte API-Endpoints

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| `GET` | `/health` | Healthcheck |
| `GET` | `/api/sources` | Alle konfigurierten Datenquellen |
| `GET` | `/api/events` | Ereignisliste mit Filterparametern |
| `GET` | `/api/events/{id}` | Detailansicht eines Ereignisses |
| `POST` | `/api/jobs/fetch` | Manueller Fetch-Trigger (Token-geschützt) |
| `GET` | `/api/stats` | Statistiken (24h/7d, Quellenstatus) |
| `GET` | `/docs` | Swagger UI (interaktive API-Doku) |

### Filter-Parameter für `GET /api/events`

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `insolvency` | bool | `true` = nur Events mit Score ≥ 0.5 |
| `max_employees` | int | Maximale Mitarbeiterzahl |
| `max_revenue` | float | Maximaler Jahresumsatz in EUR |
| `source` | string | Quellen-Name (Teilstring) |
| `q` | string | Volltextsuche im Titel |
| `limit` | int | Max. Ergebnisse (Standard: 100) |
| `offset` | int | Offset für Paginierung |

---

## Scheduler

Der Backend-Service führt täglich (Standard: 03:00 Uhr UTC) einen automatischen
Fetch aller aktiven Quellen durch. Der Zeitpunkt ist über die Umgebungsvariable
`SCHEDULER_HOUR` konfigurierbar.

**Manueller Trigger (CLI):**
```bash
cd backend
python -m app.jobs.fetch_all
```

**Manueller Trigger (API):**
```bash
curl -X POST http://localhost:8000/api/jobs/fetch \
  -H "X-Api-Token: <dein-token>"
```

---

## Datenquellen & Compliance

### ✅ Unternehmensregister / insolvenzbekanntmachungen.de

| Attribut | Wert |
|----------|------|
| **Modus** | `rss` (aktiv) |
| **Basis** | Öffentlicher RSS-Feed von insolvenzbekanntmachungen.de |
| **Rechtsbasis** | § 9 Abs. 1 HGB – amtliche Pflichtveröffentlichungen |
| **Robots.txt** | Öffentlicher Endpunkt, robots-konform |

Die Insolvenzbekanntmachungen werden vom offiziellen Portal der deutschen
Justiz veröffentlicht und sind explizit zur öffentlichen Nutzung bestimmt.
Der verwendete RSS-Feed ist ein dokumentierter, maschinell lesbarer Zugang
zu diesen Pflichtbekanntmachungen.

### ⚠️ Creditreform – DEGRADED MODE

| Attribut | Wert |
|----------|------|
| **Modus** | `degraded` (dauerhaft) |
| **Grund** | Kein öffentlicher Feed/API; robots.txt untersagt Crawling |
| **Datenpflege** | Nur manuelle Erfassung möglich |

Creditreform bietet keine öffentliche Datenschnittstelle an. Das automatisierte
Auslesen verstößt gegen die Nutzungsbedingungen und die robots.txt. Diese Quelle
ist daher **dauerhaft im degraded-Modus** und liefert keine automatischen Events.
Das Frontend kennzeichnet dies transparent.

---

## Datenmodell

```
Source     (id, name, base_url, enabled, mode, legal_note, last_fetch_at, last_fetch_status)
Company    (id, name, registry_id, employees, revenue_eur, location)
Event      (id, source_id, company_id, title, url, published_at, fetched_at,
            event_type, insolvency_score, raw_excerpt, hash, data_incomplete)
```

### Insolvenz-Scoring

Regelbasiertes Scoring über deutsche Schlüsselbegriffe:

| Begriff | Score |
|---------|-------|
| insolvenzbekanntmachung | 1.0 |
| insolvenzverfahren eröffnet | 1.0 |
| vorläufiger insolvenzverwalter | 1.0 |
| masseunzulänglichkeit | 1.0 |
| insolvenzantrag | 0.9 |
| zahlungsunfähig | 0.9 |
| insolvenzverwalter | 0.9 |
| insolvenz | 0.8 |
| überschuldung | 0.7 |
| … | … |

Ein Event gilt als **Insolvenz-Event**, wenn `insolvency_score >= 0.5`.

### KMU-Filter

Events werden **nicht verworfen**, wenn Unternehmenskennzahlen fehlen –
stattdessen werden sie als `data_incomplete = True` markiert und im UI
entsprechend gekennzeichnet.

---

## Tests ausführen

```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v
```

Abgedeckte Testbereiche:
- `test_classifier.py` – Insolvenz-Keyword-Scoring
- `test_dedup.py` – Hash-Deduplizierung
- `test_api.py` – REST-API-Filterparameter

---

## UI-Beschreibung

### Dashboard (`/`)
- **KPI-Kacheln**: Neue Treffer (24h/7d), Insolvenz-Events (24h/7d)
- **Degraded-Banner**: Warnung bei eingeschränkten Quellen
- **Filterleiste**: Suche, Insolvenz-Toggle, Max. Mitarbeiter, Max. Umsatz, Quelle
  - **KMU-Filter-Button**: Setzt sofort ≤50 MA + <10 Mio EUR
- **Ereignistabelle**: Titel (klickbar), Quelle-Badge, Datum, Score-Balken,
  Typ-Badge, Vollständigkeits-Badge, Quell-Link
- **Manueller Fetch**: Button mit Token-Eingabe

### Detailansicht (`/events/:id`)
- Alle Metadaten, Score-Visualisierung, Roh-Auszug
- Unternehmensdaten (falls vorhanden) inkl. KMU-Kennzahlen
- Vollständigkeits-Kennzeichnung

### Quellen (`/sources`)
- Status jeder Quelle (Aktiv/Degraded, letzter Fetch)
- Rechtlicher Hinweis pro Quelle
- Degraded-Banner für eingeschränkte Quellen

---

## Bekannte Einschränkungen & Datenqualität

1. **insolvenzbekanntmachungen.de RSS**: Enthält möglicherweise nicht alle
   Insolvenzverfahren zeitgleich. Tagesaktualität abhängig von der Justiz-IT.

2. **Creditreform**: Kein automatisierter Zugriff möglich. KI/Score-Werte für
   diese Quelle müssen manuell gepflegt werden.

3. **KMU-Kennzahlen**: Insolvenzbekanntmachungen enthalten typischerweise
   keine Mitarbeiter-/Umsatzdaten. Events werden als `data_incomplete` markiert.
   Eine Anreicherung über Handelsregister-Daten ist als spätere Erweiterung möglich.

4. **SQLite für MVP**: Für den Produktiveinsatz mit mehreren parallelen Zugriffen
   sollte auf PostgreSQL gewechselt werden (nur `DATABASE_URL` in `.env` anpassen).

---

## Lizenz & Rechtliches

Dieses Tool ist ein internes MVP-Werkzeug. Bitte sicherstellen, dass:
- Nur ToS- und robots.txt-konforme Endpunkte abgerufen werden.
- Personenbezogene Daten aus Insolvenzbekanntmachungen gemäß DSGVO behandelt werden.
- Die Nutzung von Creditreform-Daten ausschließlich manuell erfolgt.
