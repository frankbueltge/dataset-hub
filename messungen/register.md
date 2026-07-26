# Messregister — Go/No-Go je Quelle

Gates: siehe `TEMPLATE.md` (v0.1). Jede Zeile verweist auf ein vollständiges
Messprotokoll in `ergebnisse/`. Ein NO-GO ist ein gültiges, bleibendes Messergebnis.

| Quelle | Datum | Ergebnis | Kern der Begründung |
|---|---|---|---|
| **DataCite** | 2026-07-26 | **GO** — Adapter in Betrieb (Phase 2) | 72,7 Mio. Typ dataset; Zufallsstichprobe: 100 % Titel/Urheber/Herausgeber/URL; Cursor-Volliteration; 13.310 Updates/24 h. Auflage erfüllt: Public Data File vermessen (108,5 Mio. Records, 33 GiB, Stufe registration — `2026-07-26-datacite-dump.md`); Kern läuft inkrementell, Bulk-Bootstrap ist ein eigener späterer Schritt. |
| **Zenodo** | 2026-07-26 | **GO** — Rolle: Anreicherung | 100 % DOI/URL, 99 % Lizenz, 95,5 % Konzept-DOI, Zugangsstatus explizit; Kern kommt via DataCite. Volliteration über OAI-PMH (Search-Fenster 10k). |
| **OpenAIRE** | 2026-07-26 | ZURÜCKGESTELLT | 99,5 % der DataCite-DOIs enthalten (Überlappungsmessung) → lohnt nur für Nicht-DataCite-Anteil (~33,5 Mio. Fundstellen). Graph-API v1 anonym erreichbar, aber unvermessen; Legacy-Pfad NO-GO (10k-Fenster, oaf-Schema). |
| **EU Open Data Portal** | 2026-07-26 | NACHMESSEN | 1,76 Mio. Datasets, URL/Format 99 %; ABER Stichprobe auf 3 Kataloge verzerrt (G3 nicht beurteilbar), Such-API kappt still bei tiefen Seiten (HTTP 200, 0 Ergebnisse), Urheber/Zeitraum/Räumlichkeit fehlen auf Such-Ebene. Stratifizierte Nachmessung + Scroll/Dump-Weg. |
| **HuggingFace** | 2026-07-26 | **GO mit dokumentierter Ausnahme** (Frank, 2026-07-26) | Bestand > 120.000, Lizenz 81,5 %, gated-Stufen ablesbar, Cursor ✓; kein URL-Feld in der API → genehmigte Ausnahme: Zugriffsweg aus dem dokumentierten API-Vertrag, **Pflicht-Auflösung (HTTP) vor jeder Aufnahme** — verankert in `schema/SCHEMA.md` (Quellen-Ausnahme). Adapter: nach dem DataCite-Kern. |
| **data.gov** | 2026-07-26 | **NO-GO derzeit** — Wiedervorlage | Alle CKAN-API-Pfade 404 (strukturierte JSON-404s); Weboberfläche lebt. Kein maschinenlesbarer Erntepfad belegt. US-Lücke wird bis dahin ausgewiesen. |
| **ArcGIS Hub** | 2026-07-26 | **GO mit Auflagen** | Titel/Urheber/URL/Lizenz je 100 %; Inkrement über `filter[modified]=YYYY/MM/DD` belegt (~13.783 Änderungen/Tag). **G4 nicht erfüllt:** hartes Fenster bei Offset+Size = 10.000 (HTTP 500, kein Cursor). **Der Zähler 21,1 Mio. zählt Layer, nicht Ressourcen** — nur 51,5 % eindeutige `itemId` in der Stichprobe (ein Service 45×). Auflagen: Sparse-Fieldsets zwingend (98,3 % kleinerer Payload), Dedup auf `itemId` statt `id`, `sort=modified` unbrauchbar (Datenmüll: Zeitstempel im Jahr ~3000), Zeitscheiben-Bootstrap vor Adapterbau nachweisen. |
| **Kaggle** | 2026-07-26 | **GO mit Auflagen** | Titel/Urheber/URL/Lizenz/Aktualisierungsdatum je 100 % — wörtliche URL vorhanden, keine Ausnahme nötig. Inkrement über `sortBy=updated` belegt. **G4 nicht erfüllt:** stilles Fenster bei exakt 10.000 (Seite 501 liefert HTTP 200 mit leerem Array — sieht aus wie „fertig"). Auflagen: Retry/Resume für unangekündigte HTTP-404-Abbrüche mitten in der Iteration (in 2 von 3 Läufen beobachtet), `kaggle/meta-kaggle` als Bulk-Weg separat vermessen. |
| re3data | 2026-07-26 | Quelle der Quellen (kein Gate nötig) | 3.516 Repositorien per API; dient ab Phase 2 als Registry-Abgleich und Lieferant von Messaufträgen, nie direkt als Datensatzquelle. |

## Kandidaten aus der Vorerkundung (2026-07-26) — volle Messung ausstehend

Details: `ergebnisse/2026-07-26-vorerkundung-weitere-quellen.md`. Reihenfolge =
vorgeschlagene Priorität.

| Kandidat | Stichproben-Befund | Messauftrag |
|---|---|---|
| ~~ArcGIS Hub~~ | vermessen → GO mit Auflagen (siehe oben) | erledigt 2026-07-26 |
| ~~Kaggle~~ | vermessen → GO mit Auflagen (siehe oben) | erledigt 2026-07-26 |
| Socrata Discovery (US/EU) | US-Zähler exakt 10.000 → **mutmaßlich dasselbe 10k-Fenster wie ArcGIS und Kaggle** (siehe Querbefund unten); EU 5.584 | echten Zählweg klären (Facetten/domains), Feldabdeckung; US-Lücken-Relevanz |
| Dataverse-Netzwerk | Harvard allein 301.465 | DataCite-Überlappung messen (entscheidet Kern vs. Anreicherung) |
| OpenDataSoft-Netzwerk | 100.886 im Portalnetz | Feldabdeckung, Inkrement |
| OpenML | HTTP 504 am Messtag (Ausfall, kein Urteil) | Wiedervorlage |
| Kuratierte Listen (awesome-public-datasets, curran/data u. ä.) | 897 Links/661 Domains bzw. 55/41; Link-Rot 15 % (n=20) | eigene Familie: Listen-Parser + Pflicht-Auflösung + Urteilsroutine; primär Quelle-von-Quellen |

## Offene Entscheidungen

1. ~~HuggingFace-Ausnahme~~ — entschieden (Frank, 2026-07-26): Ausnahme genehmigt,
   eng gefasst (Pflicht-Auflösung vor Aufnahme; `schema/SCHEMA.md`).
2. Schwellenänderungen an den Gates: bisher keine.
3. Bulk-Bootstrap DataCite Public Data File (33 GiB, E-Mail-Registrierung durch
   Frank, ~650 GiB Verarbeitungsplatz): wann und wo verarbeiten?

## Querbefund: das 10.000er-Fenster (2026-07-26)

Fünf von sieben gemessenen Such-APIs kappen bei **exakt 10.000 erreichbaren Records**
(Elasticsearch-`max_result_window`): Zenodo (HTTP 400), OpenAIRE (HTTP 400), ArcGIS Hub
(HTTP 500 mit expliziter Meldung), Kaggle (**HTTP 200 mit leerem Array — stille Leere**),
mutmaßlich Socrata (Zähler exakt 10.000). Das EU-Portal kappt ebenfalls still (Seite 5000:
HTTP 200, null Ergebnisse).

**Konsequenz für jeden Adapter:** Volliteration braucht immer einen Weg *neben* der
Suche — Cursor (DataCite), OAI-PMH (Zenodo), Dump (DataCite Public Data File,
`kaggle/meta-kaggle`) oder Zeitscheiben unter 10.000 Treffern. **Und:** Eine leere Seite
darf niemals als „fertig" gelesen werden. Zwei der gemessenen Quellen signalisieren
Erfolg, wo sie kappen — eine naive Ernte hielte das für Vollständigkeit. Regel für alle
Adapter: gegen einen unabhängigen Zähler prüfen und Unvollständigkeit ins Manifest
schreiben.

## Stand

**Phase 1 abgeschlossen:** acht Quellen vermessen, eine Überlappungsmessung, eine
Klärung, eine Vorerkundung. **Phase 2 läuft** (Frank, 2026-07-26): Schema eingefroren,
DataCite-Adapter in Betrieb, erster Snapshot veröffentlicht
(`snapshot-2026-07-26`: 13.010 Einträge, 12.128 Werke).

Adapter-Warteschlange nach Messlage: DataCite (läuft) → Kaggle und ArcGIS Hub
(GO mit Auflagen) → HuggingFace (GO mit Ausnahme) → Zenodo (Anreicherung).
