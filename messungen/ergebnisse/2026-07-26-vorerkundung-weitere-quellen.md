# Vorerkundung — weitere Quellkandidaten

**Datum:** 2026-07-26 · **Anlass:** Franks Frage nach weiteren APIs/Quellen (u. a.
GitHub-Listen) · **Skript:** `skripte/vorerkundung_weitere_quellen.py` ·
**Ergebnis-JSON:** `ergebnisse/2026-07-26-vorerkundung-weitere-quellen.json` ·
**Rohdaten:** `rohdaten/vorerkundung-*.gz`

Stichproben-Zähler, keine vollen Messungen — jede Zeile, die weiterverfolgt wird,
braucht vor einem Adapter das volle Messprotokoll nach `TEMPLATE.md`.

## API-Kataloge

| Kandidat | Abfrage | Befund |
|---|---|---|
| **ArcGIS Hub** | `hub.arcgis.com/api/v3/datasets` | **21.104.755** (`meta.total`) — mit Abstand größter Neuzugang; ungeklärt, was ArcGIS alles als „dataset" zählt (Layer? Karten?) |
| **Dataverse (Harvard)** | `dataverse.harvard.edu/api/search?type=dataset` | **301.465** — eine Installation eines Netzwerks aus Dutzenden; gleiche API überall; DOIs → DataCite-Überlappung messen |
| **OpenDataSoft-Netzwerk** | `data.opendatasoft.com/api/explore/v2.1/catalog/datasets` | **100.886** über das gesamte Portalnetz |
| **Socrata Discovery US** | `api.us.socrata.com/api/catalog/v1?only=datasets` | resultSetSize **exakt 10.000 — verdächtig runde Zahl, mutmaßlich gekappter Zähler** (Atlas-Lektion: Konstanten misstrauen); echter Zählweg zu klären. Relevant für die US-Lücke |
| **Socrata Discovery EU** | `api.eu.socrata.com/api/catalog/v1?only=datasets` | 5.584 |
| **Kaggle** | `kaggle.com/api/v1/datasets/list` (unauthentifiziert!) | HTTP 200; Records tragen **wörtliches URL-Feld, Lizenzname, Urheber** — im Gegensatz zu HuggingFace. Kein Zähler in der Antwort; Rate-Limits/Inkrement ungemessen |
| **OpenML** | `openml.org/api/v1/json/data/list` | **HTTP 504 am Messtag** — Ausfall, kein Urteil. Wiedervorlage |
| data.gov DCAT-Export | `catalog.data.gov/data.json` (HEAD) | 404 — auch dieser Weg existiert nicht; Wiedervorlage-Auftrag aus der Klärung bleibt |

## Kuratierte GitHub-Listen (Franks Hinweis)

| Liste | Links | Domains | Letzter Push | Link-Rot-Ministichprobe |
|---|---|---|---|---|
| `awesomedata/awesome-public-datasets` (77.735 ★) | 897 | **661** | 2026-07-13 (lebendig) | n=20: 17× 2xx, **3× 4xx (15 %)** |
| `curran/data` (531 ★) | 55 | 41 | 2025-12-25 | — |

**Einordnung:** Das sind keine Kataloge (keine strukturierten Metadaten, keine
Inkrement-API), sondern **kuratierte Verzeichnisse** — und mit 661 Domains ist die
awesome-Liste vor allem eine **Quelle von Quellen** (wie re3data, nur für den Long
Tail jenseits der Wissenschafts-/Behördenwelt). Vorgeschlagene Behandlung als eigene
Quellfamilie „kuratierte Listen": deterministischer Listen-Parser (Links wörtlich aus
dem README) → **Pflicht-Auflösung jedes Links** (die 15 % Rot zeigen warum) →
Urteilsroutine ordnet zu: (a) Katalog dahinter → Messauftrag ins Register,
(b) Einzeldatensatz → Aufnahme als Eintrag mit dünnen, ehrlichen Metadaten
(fehlende Felder bleiben leer), (c) tot/kein Datensatz → Ablehnungsregister.

## Konsequenzen

1. **Die US-Lücke (data.gov NO-GO) ist teilweise anders schließbar:** Socrata
   Discovery + ArcGIS Hub tragen große Teile der US-Kommunal-/Bundesstaats- und
   Geodaten-Portale.
2. **Kaggle schlägt HuggingFace bei der URL-Frage:** wörtliches URL-Feld vorhanden —
   die HF-Grundsatzentscheidung (Ausnahme oder NO-GO) bleibt davon unberührt, aber
   Kaggle braucht sie nicht.
3. Volle Messaufträge einsortiert in `register.md` (Abschnitt Kandidaten).
