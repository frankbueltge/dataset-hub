# CLAUDE.md — dataset-hub

Maschinenlesbarer Nachweis öffentlich zugänglicher Datensätze — Infrastruktur der
research ecology (frankbueltge.de), **kein Lab-Experiment**. Zwei gleichrangige
Nutzungen: Hub für Forschende und abfragbare Snapshot-Grundlage für die Pipelines.

**Maßgebliches Design (vor jeder Arbeit lesen):**
`frankbueltge.de → docs/superpowers/specs/2026-07-26-dataset-hub-design.md`
(Identitätsmodell Fundstelle/Fassung/Datensatz, Merge-Stufen R1–R4, Zugangsstufen,
Snapshot-Vertrag). Startauftrag mit den verbindlichen Bauregeln:
`frankbueltge.de → docs/research/2026-07-26-dataset-hub-startauftrag.md`.

**Der Zweck ist am 27.07. neu gefasst worden — sie geht dem Startauftrag vor:**
`frankbueltge.de → docs/design/2026-07-27-register-neufassung.md`. Das Register ist
KEIN „größtmöglicher Nachweis" mehr, sondern eine **kuratierte Meta-Sammlung über
viele öffentliche Quellen**. Wo der Startauftrag Vollständigkeit verlangt, gilt er
nicht mehr; seine Bauregeln (nichts erfinden, Ausfälle vermerken, keine Modell-APIs)
gelten unverändert weiter.

## Phase

**Phase 2 — Bestand.** Vier Ernte-Adapter laufen (datacite, arcgis, huggingface,
kaggle — kaggle rechtlich zurückgehalten). Ein neuer Adapter entsteht weiterhin
NICHT, solange `messungen/register.md` für die Quelle kein GO enthält. Gates stehen
in `messungen/TEMPLATE.md`; Schwellenänderungen nur mit Begründung im Register.

## Das Relevanzkriterium (Neufassung §4, zwei Stufen)

| Stufe | wo | was |
|---|---|---|
| 1 — Materialgüte | `pipeline/relevanz.py` | entscheidet die **Aufnahme**: keine Massenregistrierungen, benannte Lizenz. Ergebnis ist der Snapshot der Praxen |
| 2 — Kernbestand | `pipeline/kernbestand.py` | ein **Merkmal** am Eintrag: nur der Kernbestand bekommt Unterseiten und Sichtbarkeit auf der Website |

- **`register/massenherausgeber.json` ist Teil der Schranke.** Fehlt die Datei, bricht
  der Bestandsbau ab — er füllt sich nie stillschweigend wieder mit Serien.
- Der Kernbestand-Sieb ist **dreiwertig**: `regel` (Begriff im Titel entscheidet),
  `grenzfall` (wartet auf die Urteilsroutine), kein Treffer. **Unbeurteilte Grenzfälle
  sind NICHT im Kernbestand** — die Website behauptet keine Relevanz, die niemand
  geprüft hat.
- **Der DataCite-Bulk ist Steinbruch, kein Bestand** (Neufassung §5). Er liegt in
  `steinbruch/`, wird gezielt abgebaut und nie als Ganzes eingelesen; `baue_bestand.py`
  überspringt Dateien mit `-dump-` im Namen zusätzlich als Schutz.

## Verbindliche Regeln (Kurzform — Langform im Startauftrag)

- Nichts erfinden; leere Felder bleiben leer.
- Identifier prüfen heißt: HTTP-Antwort geholt. Nie URLs konstruieren, auch nicht
  aus Titel und Muster.
- Deterministisch, wo es geht. **Kein Modell-API-Aufruf in Pipelines/Skripten**
  (kein API-Guthaben; Urteilsschritte laufen als Claude-Code-Routine unter dem Abo).
- Ablehnungen mit Grund mitschreiben; Ausfälle vermerken, nie überbrücken
  (leer ≠ nicht erreichbar).
- Jede Zahl in einem Messbericht stammt aus `messungen/ergebnisse/*.json`, und jedes
  Ergebnis-JSON ist durch Rohdaten in `messungen/rohdaten/` (gzip) gedeckt.
- Messskripte: Python 3, nur Standardbibliothek, lesende API-Zugriffe mit Drossel.

## Arbeitsregeln (Standing, aus dem Workspace)

- **Keine KI-Produkt-Credits in Git:** nie `Co-Authored-By: Claude …`, „Generated with …"
  o. Ä. in Commits/PRs/Inhalten.
- Git-Identität: `Frank Bültge <f.bueltge@gmail.com>` — NIEMALS `frank@bueltge.de`
  (gehört einer anderen realen Person).
- Lizenz: Code Apache 2.0, Werke/Texte CC BY 4.0, Katalog-Metadaten CC0 (Frank, 2026-07-26).

## Kommandos

```bash
cd messungen/skripte
python3 messe_<quelle>.py        # schreibt ergebnisse/<datum>-<quelle>.json + rohdaten/*.gz

cd pipeline
python3 ernte_<quelle>.py        # Rohernte → fundstellen/*.jsonl.gz + manifeste/
python3 baue_bestand.py          # Fundstellen → bestand/hub.sqlite (beide Relevanzstufen)
python3 baue_snapshot.py         # Bestand → snapshots/ (Vertrag: SNAPSHOT-API.md)
python3 -m unittest discover -s tests

cd oberflaeche
python3 generiere_index.py       # Bestand → public/daten/ (NUR Kernbestand)
```
