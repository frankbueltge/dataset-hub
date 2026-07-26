# Messregister — Go/No-Go je Quelle

Gates: siehe `TEMPLATE.md` (v0.1). Jede Zeile verweist auf ein vollständiges
Messprotokoll in `ergebnisse/`. Ein NO-GO ist ein gültiges, bleibendes Messergebnis.

| Quelle | Datum | Ergebnis | Kern der Begründung |
|---|---|---|---|
| **DataCite** | 2026-07-26 | **GO** — erster Adapter (Phase 2) | 72,7 Mio. Typ dataset; Zufallsstichprobe: 100 % Titel/Urheber/Herausgeber/URL; Cursor-Volliteration; 13.310 Updates/24 h. Auflage: Public Data File vermessen (Bulk vs. API). |
| **Zenodo** | 2026-07-26 | **GO** — Rolle: Anreicherung | 100 % DOI/URL, 99 % Lizenz, 95,5 % Konzept-DOI, Zugangsstatus explizit; Kern kommt via DataCite. Volliteration über OAI-PMH (Search-Fenster 10k). |
| **OpenAIRE** | 2026-07-26 | ZURÜCKGESTELLT | 99,5 % der DataCite-DOIs enthalten (Überlappungsmessung) → lohnt nur für Nicht-DataCite-Anteil (~33,5 Mio. Fundstellen). Graph-API v1 anonym erreichbar, aber unvermessen; Legacy-Pfad NO-GO (10k-Fenster, oaf-Schema). |
| **EU Open Data Portal** | 2026-07-26 | NACHMESSEN | 1,76 Mio. Datasets, URL/Format 99 %; ABER Stichprobe auf 3 Kataloge verzerrt (G3 nicht beurteilbar), Such-API kappt still bei tiefen Seiten (HTTP 200, 0 Ergebnisse), Urheber/Zeitraum/Räumlichkeit fehlen auf Such-Ebene. Stratifizierte Nachmessung + Scroll/Dump-Weg. |
| **HuggingFace** | 2026-07-26 | **ENTSCHEIDUNG FRANK** | Bestand > 120.000 (Zähl-Iteration gekappt), Lizenz 81,5 %, gated-Stufen ablesbar, Cursor ✓ — aber **0 % wörtliche Zugriffs-URL** (auch Detail-Endpunkt). Optionen: dokumentierte Ausnahme (URL aus API-Vertrag + Pflicht-Auflösung vor Aufnahme) oder NO-GO. |
| **data.gov** | 2026-07-26 | **NO-GO derzeit** — Wiedervorlage | Alle CKAN-API-Pfade 404 (strukturierte JSON-404s); Weboberfläche lebt. Kein maschinenlesbarer Erntepfad belegt. US-Lücke wird bis dahin ausgewiesen. |
| re3data | 2026-07-26 | Quelle der Quellen (kein Gate nötig) | 3.516 Repositorien per API; dient ab Phase 2 als Registry-Abgleich und Lieferant von Messaufträgen, nie direkt als Datensatzquelle. |

## Kandidaten aus der Vorerkundung (2026-07-26) — volle Messung ausstehend

Details: `ergebnisse/2026-07-26-vorerkundung-weitere-quellen.md`. Reihenfolge =
vorgeschlagene Priorität.

| Kandidat | Stichproben-Befund | Messauftrag |
|---|---|---|
| ArcGIS Hub | 21,1 Mio. laut `meta.total` | Was zählt als „dataset"? Feldabdeckung, Inkrement, Volliteration |
| Kaggle | unauthentifiziert nutzbar; wörtliche URL + Lizenz + Urheber je Record | Zähler (Iteration), Rate-Limits, Inkrement-Weg |
| Socrata Discovery (US/EU) | US-Zähler exakt 10.000 → mutmaßlich gekappt; EU 5.584 | echten Zählweg klären (Facetten/domains), Feldabdeckung; US-Lücken-Relevanz |
| Dataverse-Netzwerk | Harvard allein 301.465 | DataCite-Überlappung messen (entscheidet Kern vs. Anreicherung) |
| OpenDataSoft-Netzwerk | 100.886 im Portalnetz | Feldabdeckung, Inkrement |
| OpenML | HTTP 504 am Messtag (Ausfall, kein Urteil) | Wiedervorlage |
| Kuratierte Listen (awesome-public-datasets, curran/data u. ä.) | 897 Links/661 Domains bzw. 55/41; Link-Rot 15 % (n=20) | eigene Familie: Listen-Parser + Pflicht-Auflösung + Urteilsroutine; primär Quelle-von-Quellen |

## Offene Entscheidungen

1. **HuggingFace-Ausnahme** (siehe oben) — Franks Entscheidung.
2. Schwellenänderungen an den Gates: bisher keine.

## Stand Phase 1

Sechs Quellen vermessen, eine Überlappungsmessung, eine Klärung. Ergebnis: **ein
klarer Erst-Adapter-Kandidat (DataCite)**, eine Anreicherungsquelle (Zenodo), drei
Wiedervorlagen, ein NO-GO. Nächster Schritt (Phase 2) laut Design: Schema v0.1
einfrieren, Fundstellen-Store, DataCite-Adapter, Dedup R1–R4, erster Snapshot —
nach Franks Kenntnisnahme dieses Registers.
