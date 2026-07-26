# Klärungsprotokoll — data.gov (CKAN-API antwortet 404)

**Datum:** 2026-07-26 · **Skript:** `skripte/klaere_datagov.py` · **Ergebnis-JSON:**
`ergebnisse/2026-07-26-datagov-klaerung.json`

## Befunde (alle tatsächlich abgerufen)

| Endpunkt | Status | Befund |
|---|---|---|
| `catalog.data.gov/api/3/action/package_search` | **404** | JSON `{"detail":{},"message":"Not Found"}` |
| `catalog.data.gov/api/action/package_search` | **404** | dito |
| `catalog.data.gov/api/3/action/site_read` | **404** | dito |
| `catalog.data.gov/api/3` | **404** | dito |
| `catalog.data.gov/dataset` (HTML) | 200 | Katalog-Weboberfläche lebt |
| `www.data.gov` | 200 | Portal lebt |
| `data.gov/developers/` | **404** | Entwicklerseite unter diesem Pfad verschwunden |
| `api.data.gov` | 200 | API-Programm-Seite erreichbar |

## Deutung (als Vermutung gekennzeichnet)

Die 404-Antworten sind strukturierte JSON-Antworten eines modernen Backends, keine
CKAN-Fehler — der Katalog läuft mutmaßlich auf einem neuen Unterbau, die klassische
CKAN-API ist unter den Standardpfaden nicht mehr öffentlich. Das ist eine Vermutung;
belegt ist nur: **kein maschinenlesbarer Erntepfad gefunden.**

## Bewertung → **NO-GO derzeit**, Wiedervorlage

Wiedervorlage-Aufträge: (1) api.data.gov-Programm prüfen (Key-basierter Zugang zum
Katalog?), (2) GSA-Quellcode/Harvest-Infrastruktur auf GitHub sichten, (3) prüfen, ob
ein DCAT-US-Export existiert. **Lücke ehrlich benennen:** US-Bundesdaten sind durch
das EU-Portal nicht abgedeckt; solange hier kein Weg existiert, fehlt dieser Bestand
und der Hub sagt das dazu.
