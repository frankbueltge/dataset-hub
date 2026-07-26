# CLAUDE.md — dataset-hub

Maschinenlesbarer Nachweis öffentlich zugänglicher Datensätze — Infrastruktur der
research ecology (frankbueltge.de), **kein Lab-Experiment**. Zwei gleichrangige
Nutzungen: Hub für Forschende und abfragbare Snapshot-Grundlage für die Pipelines.

**Maßgebliches Design (vor jeder Arbeit lesen):**
`frankbueltge.de → docs/superpowers/specs/2026-07-26-dataset-hub-design.md`
(Identitätsmodell Fundstelle/Fassung/Datensatz, Merge-Stufen R1–R4, Zugangsstufen,
Snapshot-Vertrag). Startauftrag mit den verbindlichen Bauregeln:
`frankbueltge.de → docs/research/2026-07-26-dataset-hub-startauftrag.md`.

## Phase

**Phase 1 — Messrunde.** Es gibt KEINE Ernte-Adapter, und es darf keiner entstehen,
solange `messungen/register.md` für die Quelle kein GO enthält. Gates stehen in
`messungen/TEMPLATE.md`; Schwellenänderungen nur mit Begründung im Register.

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
```
