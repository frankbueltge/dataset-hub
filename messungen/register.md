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

## Rechtliche Grundlage je Quelle (Gate G5, geprüft 2026-07-26)

Kein Rechtsrat — gelesen, zitiert, und wo mehrdeutig, als mehrdeutig vermerkt.

| Quelle | Fundstelle | Befund | Folge |
|---|---|---|---|
| **DataCite** | `support.datacite.org/docs/datacite-data-file-use-policy` | „To the extent possible under law, **DataCite e.V. has waived all copyright and related or neighboring rights** to DataCite Data File. The DataCite Data File includes all DOIs and deposited metadata in our database." — CC0, ausdrücklich auch Datenbankrechte | **frei.** Speichern, weiterveröffentlichen, Beschreibungen im Wortlaut: alles gedeckt |
| **Kaggle** | `kaggle.com/terms`, Abschnitt Nutzungsbeschränkungen | Untersagt ist, die Dienste so zu nutzen, dass man *„‚Crawls,‘ ‚scrapes,‘ or ‚spiders‘ any page, data, or portion of or relating to the Services or Content (through use of manual or automated means)"* sowie *„Copies or stores any significant portion of the Content"* | **zurückgehalten.** Siehe unten |
| **ArcGIS Hub** | Lizenz je Eintrag in der API (`license`, `structuredLicense`) | Discovery-Schicht über offene Verwaltungsdaten; jeder Eintrag trägt seine eigene Lizenz. Im geernteten Bestand: 635 CC-BY-4.0, 160 ODbL, 113 CC0, 54 CC-BY-SA, 18 PDDL — aber **3.180 `custom` und 86 `none`** | **bedingt.** Metadaten sind Fakten (Titel, Organisation, URL); Beschreibungen aus `custom`/`none`-Einträgen NICHT im Wortlaut veröffentlichen, bis die Einzellizenz ausgewertet wird |
| **HuggingFace** | `huggingface.co/terms-of-service` | Für öffentliche Repositorien: *„you grant each User a perpetual, irrevocable, worldwide, royalty-free, non-exclusive license to use, display, publish, reproduce, distribute, and make derivative works of your Content **through our Services and functionalities**"* | **bedingt.** Der Zusatz „through our Services" lässt offen, ob die Erlaubnis außerhalb der Plattform trägt. Bei 20 Einträgen derzeit ohne Gewicht; vor einem größeren Lauf klären |

### Nachtrag 2026-07-27: Richtlinie erneut gelesen

Anlass: Der Bulk-Abbau aus dem DataCite Public Data File hat die Nutzung von einer
API-Ernte (13.010 Einträge) auf einen Massen-Extrakt verschoben (56.620.404 gelesen,
16.443 aufgenommen). Bei dieser Größenordnung trägt das Datenbankherstellerrecht
(§ 87b UrhG) die Frage, nicht mehr das Urheberrecht am Einzeldatensatz.

Der CC0-Verzicht gilt unverändert und deckt ausdrücklich auch Datenbankrechte. Drei
Punkte der Richtlinie standen aber noch nicht im Register:

1. **Nicht gedeckt: Persönlichkeitsrechte.** Der Verzicht erstreckt sich ausdrücklich
   NICHT auf „rights of individuals featured in the data, including privacy and
   publicity rights". Die Urhebernamen und ORCID-Kennungen im Bestand sind damit
   unsere Verantwortung, nicht durch CC0 freigestellt. Stand 27.07.: **20.082
   verschiedene Namen, 15.240 ORCID-Nennungen** im Kernbestand. Abgedeckt über die
   Datenschutzerklärung der Site (Art.-21-Widerspruch, Entfernungsweg, Archiv-Hinweis).
2. **Nicht gedeckt: die verlinkten Ressourcen selbst.** Der Verzicht betrifft die
   Metadaten, nicht die Datensätze, auf die sie zeigen. Das Register verweist nur —
   es kopiert keine Inhalte der Zielressourcen.
3. **Community-Normen (erbeten, nicht verpflichtend):** Namensnennung von DataCite als
   Quelle, keine sinnentstellende Veränderung, Rückmeldung zur Nutzung. Die
   Namensnennung ist am 27.07. auf der Registerseite ergänzt worden — nicht weil sie
   verlangt wird, sondern weil dieselbe Ökologie für ihre eigenen Werke auf
   Namensnennung besteht.

Ebenfalls vermerkt: DataCite gibt keine Gewährleistung und übernimmt keine Haftung
für die Nutzung der Datei.

### Kaggle: zurückgehalten (2026-07-26)

Die 9.991 Einträge sind **aus dem Bestand genommen** (`schranken.py:
QUELLEN_ZURUECKGEHALTEN`, Grundcode `quelle-rechtlich-ungeklaert`), und die Inhalte
sind **gelöscht** — Rohernten aus Release und Arbeitsverzeichnis, Kennungen aus
Ablehnungs- und Fundstellen-Tabelle.

Die erste Fassung dieses Eintrags hieß „die Rohernten bleiben im Archiv". Das war
falsch: Wenn das Speichern wesentlicher Teile untersagt ist, ist auch das Archiv
Speichern — und unseres liegt öffentlich (Frank, 2026-07-26; siehe
`VERFAHRENSNOTIZEN.md`). Erhalten bleiben nur die Ernte-Manifeste und ein
Sammeleintrag im Ablehnungsregister: unsere Buchführung über unser eigenes Handeln,
ohne Fremdinhalt.

**Nachtrag 2026-07-27:** Die Löschung betraf die Ernten, nicht die Messrohdaten —
vier Dateien (rund 117 KB, größte mit 200 Datensätzen) lagen weiter in
`messungen/rohdaten/`. Sie sind jetzt entfernt. Damit ist die Kaggle-Messung
(`2026-07-26-kaggle.md`) **nicht mehr durch Rohdaten gedeckt**; ihre Zahlen bleiben
im Bericht, sind aber nicht nachrechenbar. Das ist der Preis der strengeren Lesart
und hier gewollt. In der Git-Historie bleiben die Dateien abrufbar; sie dafür
umzuschreiben wäre unverhältnismäßig.

Abwägung, offen dargelegt: Wir haben die **dokumentierte öffentliche API** genutzt
(`/api/v1/datasets/list`), nicht die Website gescrapt — programmatischer Zugriff ist
dort ersichtlich vorgesehen. Die zweite Klausel steht dem aber unabhängig davon
entgegen: Wir speichern rund 10.000 Datensatz-Beschreibungen, und ob das ein
„significant portion of the Content" ist, kann man kaum verneinen. Solange das nicht
geklärt ist, wird nicht veröffentlicht.

**Wege zurück:** (1) Anfrage an Kaggle mit Beschreibung des Vorhabens und Bitte um
Bestätigung; (2) Beschränkung auf einen Umfang, der ersichtlich nicht „significant"
ist; (3) endgültiges NO-GO. Bis dahin bleibt die Zeile in `QUELLEN_ZURUECKGEHALTEN` —
sie zu entfernen ist die Rücknahme.

### Der Adapter wird gar nicht gebraucht (Befund 2026-07-26, abends)

Auf Franks Frage „werden die von anderen auch verlinkt" gemessen: **Kaggle registriert
seine Datensätze selbst als DOIs bei DataCite.** Abfrage
`api.datacite.org/dois?query=publisher:"Kaggle"&resource-type-id=dataset` →
**62.274 Treffer**, Präfix `10.34740`, Beispiel `10.34740/kaggle/dsv/18364137` mit
`url = https://www.kaggle.com/dsv/18364137`.

Damit liegen die Metadaten dieser Datensätze **in DataCites CC0-Bestand** — durch
Kaggles eigene, bewusste Handlung. Wir bekommen sie also ohnehin, über den
DataCite-Adapter, rechtlich einwandfrei und in **sechsfacher Menge** gegenüber den
9.991, die wir über die API genommen hatten. Im bisherigen 24-Stunden-Fenster sind
bereits 48 solcher Einträge im Bestand.

**Konsequenz:** Der Kaggle-Adapter (`pipeline/ernte_kaggle.py`) ist überflüssig, nicht
nur zurückgehalten. Er bleibt vorerst als Code stehen, wird aber nicht betrieben; die
Abdeckung entsteht über DataCite. Die Lehre ist allgemeiner: **Bevor eine Quelle einen
eigenen Adapter bekommt, prüfen, ob sie ihre Metadaten bereits in ein offenes Register
einspeist.** Das ist nicht nur sauberer, sondern meist auch vollständiger — und es
erspart genau die Grauzone, in die wir hier geraten sind.

*(Nebenbefund: `kaggle.com/robots.txt` liefert keine robots.txt, sondern die
Startseiten-HTML — eine maschinenlesbare Crawling-Regel existiert dort am
Standardpfad nicht.)*

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
