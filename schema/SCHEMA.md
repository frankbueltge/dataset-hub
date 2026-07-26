# Schema v0.2.0 — Stand 2026-07-26

**Änderung 0.1.0 → 0.2.0 (additiv):** `zugang.geprueft` erhält den Wert `versucht`.
Anlass: Beim ersten Auflösungslauf antworteten 53 von 200 Zugriffswegen mit HTTP 403 —
alle vom selben Host (GBIF), der automatisierten Zugriff generell abweist, während
seine API dieselbe Ressource mit 200 ausliefert. Ohne eigenen Wert sähe „geprüft, Host
verweigert" aus wie „nie geprüft" — genau die Verwechslung, die die Regel „Ausfälle
vermerken, nie überbrücken" verbietet.

Maßgebliches Design: `frankbueltge.de → docs/superpowers/specs/2026-07-26-dataset-hub-design.md`.
Versionierung: SemVer. Brechende Änderungen erhöhen die Major-Version; Pipelines der
Ökologie pinnen die Major-Version des Snapshots. Maschinenlesbar:
`fundstelle.schema.json`, `eintrag.schema.json`.

## Fundstelle (Rohernte, unantastbar)

| Feld | Inhalt |
|---|---|
| `quelle` | Quellkennung, z. B. `datacite` |
| `quell_id` | quell-native ID (bei DataCite: normalisierter DOI, kleingeschrieben, ohne Resolver-Präfix) |
| `geerntet` | Zeitstempel UTC |
| `adapter_version` | Version des erntenden Adapters |
| `roh` | Quellmetadaten wörtlich, unverändert |

Fundstellen werden nie editiert. Ablage: `fundstellen/*.jsonl.gz` (nicht in Git;
Snapshot-Release-Assets), Manifeste mit Zähler + SHA-256 in `fundstellen/manifeste/`.

## Eintrag (abgeleitet, deterministisch reproduzierbar)

Abgeleitet aus Fundstellen + `journal/entscheidungen.jsonl`. Leere Felder bleiben leer.

| Feld | Inhalt | DCAT |
|---|---|---|
| `id` | `dh-` + sha256(`<pid_schema>:<pid_wert>`)[:16] — opak, stabil, nie wiederverwendet | — |
| `werk_id`, `fassung_id` | Gruppen-IDs aus Dedup R1–R4 (Repräsentant = kleinste Mitglieds-ID) | — |
| `granularitaet` | `collection` \| `dataset` \| `file` \| `service` (Quell-Behauptung) | Typ |
| `titel`, `beschreibung` | wörtlich aus Quelle, nie generiert | dct:title/description |
| `urheber[]` | `{name, orcid?}` | dct:creator |
| `herausgeber` | Name | dct:publisher |
| `publikationsjahr`, `daten[]` | Jahr; Datumsangaben wörtlich (`{datum, typ}`) | dct:temporal |
| `raeumlichkeit[]` | wörtlich (z. B. DataCite geoLocations) | dct:spatial |
| `lizenz` | `{id, roh[]}` — id nur, wenn die Quelle einen Identifier liefert | dct:license |
| `zugang` | `{stufe, url, geprueft, geprueft_am, http_status, finale_url}` | dct:accessRights |
| `identifikatoren[]` | `{schema, wert}` | dct:identifier |
| `relationen[]` | `{typ, ziel_schema, ziel}` — nur quellen-behauptet | dct:relation |
| `fundstellen[]` | Herkunft: `{quelle, quell_id, geerntet, adapter_version}` | dct:provenance |
| `status` | `ungeprueft` \| `geprueft` \| `markiert` \| `zurueckgezogen` | — |

### Vokabular `zugang.stufe`

`open` · `registration` · `request` · `embargoed` (aufnahmefähig) — `purchase` ·
`closed` (nicht aufnahmefähig, Ablehnungsregister). **Leer = von der Quelle nicht
angegeben** (zulässig; DataCite liefert keine Zugangsstufe — sie bleibt leer, bis
Prüfung oder Urteilsroutine sie belegt).

### Vokabular `zugang.geprueft`

`none` (nicht geprüft) · **`versucht`** (aufgelöst, aber nicht bestätigt: der Host
antwortete nicht mit 2xx — `http_status` sagt warum; 403 heißt meist Bot-Schutz, nicht
toter Link) · `landing` (Landing-URL per HTTP aufgelöst, 2xx) · `download` (Datenabruf
geprüft). Ein Eintrag behauptet nie mehr, als geprüft wurde — und nie weniger, als
tatsächlich versucht wurde.

## Harte Schranken der Auto-Aufnahme

Titel vorhanden · Zugriffs-URL wörtlich vorhanden · (Urheber ODER Herausgeber)
vorhanden · Quell-PID vorhanden · Quellstatus nicht zurückgezogen · Zugangsstufe
nicht nachweislich ausgeschlossen. Abgelehntes → `register/ablehnungen.jsonl` mit
Grundcode. Alles Aufgenommene startet als `status: ungeprueft`.

## Dedup-Stufen (automatisch, nur deterministisch)

R1 gleiche normalisierte PID → gleiche Fassung · R2 quellen-behauptete Relation
(`IsIdenticalTo` → Fassung; `IsVersionOf`/`HasVersion`/`IsNewVersionOf`/
`IsPreviousVersionOf` → Werk) · R3 identische finale URL nach tatsächlicher
HTTP-Auflösung (beide 2xx, finale URL kein Wurzelpfad) → Fassung · R4 deklarierte
Aggregatorkopie → Kopie-Vermerk. Ähnlichkeit führt NIE automatisch zusammen;
Urteils-Merges stehen als Ereignisse in `journal/entscheidungen.jsonl`
(`{datum, typ: "merge", ebene: "werk"|"fassung", mitglieder: [ids], beleg, quelle}`)
— Rücknahme = Revert des Journal-Eintrags + Neubau.

## Snapshot-Vertrag (die Abfrage-API)

Release-Tag `snapshot-YYYY-MM-DD` mit Assets: `hub-<datum>.sqlite.gz` (Bestand,
inkl. FTS5-Volltextindex über Titel/Beschreibung), Rohernten (`*.jsonl.gz`),
`manifest.json` (schema_version, Zähler, SHA-256 aller Assets, Quellfenster).
Manifest zusätzlich in Git (`snapshots/`). Pipelines laden das jüngste
`snapshot-*`-Release, prüfen `schema_version`-Major und fragen lokal per SQL ab.
Parquet-Ausgabe: vorgesehen, in v0.1 zurückgestellt (Standardbibliothek-Gebot;
Vermerk statt stiller Lücke).

## Quellen-Ausnahme (dokumentiert)

**HuggingFace (Frank, 2026-07-26):** Die Quelle führt kein URL-Feld; der Zugriffsweg
darf ausnahmsweise aus dem dokumentierten API-Vertrag der Quelle gebildet werden
(`huggingface.co/datasets/<id>`), **aber kein solcher Eintrag wird ohne erfolgreiche
HTTP-Auflösung aufgenommen** (`zugang.geprueft` mindestens `landing`). Die Ausnahme
gilt je Quelle, nie pauschal.
