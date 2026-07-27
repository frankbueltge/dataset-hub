# Messprotokoll — Wer registriert massenhaft? (exakt, alle Rohernten)

**Datum:** 2026-07-27 · **Verfahren:** vollständiger Durchlauf aller lokalen Rohernten,
keine Stichprobe · **Grundlage:** `2026-07-27-herausgeber-gesamt.json`
(volle Zählung: `rohdaten/2026-07-27-herausgeber-gesamt-vollstaendig.json.gz`)

**56.640.014 Zeilen · 18.350 Herausgeber · 0 kaputte Zeilen · 118 Dateien**
(davon 56.633.414 aus dem DataCite-Bulk, 6.300 ArcGIS, 300 HuggingFace)

Anlass: Die Neufassung des Registerzwecks braucht eine Aufnahmeschranke gegen
Massenregistrierungen. Die bisherige Grundlage war eine 400.000er-Stichprobe
(`2026-07-27-dump-zusammensetzung.md`). Für eine Schranke, die dauerhaft über Aufnahme
und Ablehnung entscheidet, ist das zu wenig.

## 1. Das erste Kriterium war falsch

Der erste Ansatz maß die **Titel-Wiederholungsrate**: 1 − (verschiedene Titelmuster /
gezählte Titel), Ziffernfolgen zu `#` normalisiert. Am lokalen Bestand vom 26.07. sah
das nach einer sauberen Trennung aus — Massenregistranten ab 0,89, Repositorien bei
0,53, nichts dazwischen.

**Über alle Quellen gemessen bricht die Trennung zusammen.** Die Rate ist
größenabhängig: je mehr Einträge, desto eher sättigt die Musterzahl.

| | Einträge | Muster | Rate |
|---|---|---|---|
| DataverseNO | 139.699 | 12.119 | 0,913 |
| Kaggle | 50.266 | 9.555 | 0,810 |

DataverseNO führt 12.119 verschiedene Titelmuster — ein vielfältiges Repositorium.
Seine Rate liegt nur deshalb hoch, weil `n` groß ist. Eine Schwelle bei 0,80 hätte
Kaggle, DataverseNO, UCLA Dataverse, Texas Data Repository und das CERN Open Data
Portal ausgeschlossen: gerade die Quellen, die vielfältige Datensätze liefern.

## 2. Das tragfähige Maß: Einträge je Titelmuster

Nicht die Rate, sondern **wie viele Einträge sich einen Titel teilen**.

| je Muster | Einträge | Muster | Herausgeber |
|---:|---:|---:|---|
| 196.234 | 1.177.402 | 6 | Cambridge Crystallographic Data Centre |
| 157.320 | 314.639 | 2 | Data MIRRI |
| 110.383 | 3.201.093 | 29 | UNITE Community |
| 108.144 | 29.198.792 | 270 | National Institute for Fusion Science |
| 19.716 | 492.888 | 25 | Environmental Molecular Sciences Laboratory |
| 3.050 | 4.007.397 | 1.314 | GBIF („Occurrence Download") |
| 100 | 60.448 | 604 | Institut français d'archéologie orientale |
| — | | | **Schwelle 100** |
| 16,5 | 1.036.508 | 62.935 | Zenodo |
| 15,6 | 58.687 | 3.753 | UCLA Dataverse |
| 11,5 | 139.699 | 12.119 | DataverseNO |
| 5,3 | 50.266 | 9.555 | Kaggle |

Die Schwelle liegt bei **100** — am oberen Rand der Lücke, bewusst vorsichtig, damit
kein Repositorium hineinrutscht. Ergebnis: **28 Herausgeber, 40,2 Mio. Fundstellen.**

## 3. Zwei blinde Flecken — benannt, nicht weggerechnet

**Die Musterzählung ist bei 50.000 gekappt.** Sonst müsste ein Herausgeber mit 30 Mio.
Einträgen 30 Mio. Titel im Arbeitsspeicher halten. Für 15 Herausgeber ist die gemeldete
Musterzahl deshalb eine Untergrenze und das Verhältnis eine **Obergrenze** — daraus
lässt sich eine Aufnahme nie begründen. Die Kappung trifft erwartungsgemäß die großen
Repositorien (Zenodo, figshare, Harvard Dataverse, PANGAEA, Mendeley, Dryad), die
ohnehin nicht auf die Liste gehören — mit einer Ausnahme:

- **Distributed System of Scientific Collections**, 5.030.937 Einträge, ≤ 93 je Muster.
  Die Titel sind zoologische und botanische Binomen mit Autorschaft — Bestimmungen
  einzelner physischer Belege. Per Urteil aufgenommen.

**Kleine Serien fallen durch jede Schwelle.** Der Consiglio Nazionale delle Ricerche
hat im ganzen Bulk 4.871 Einträge auf 520 Muster (9,4 je Muster), aber die Titel sind
reine Inventarnummern eines epigraphischen Korpus: „Ja #" 824-mal, „CIH #" 695-mal,
„al-Jawf #.#" 177-mal. Ein Identifikator je Inschrift. Per Urteil aufgenommen.

Beide Urteile stehen mit Beleg in `register/massenherausgeber-urteile.json` und
behalten in der abgeleiteten Liste ihre Herkunft (`herkunft: "urteil"` statt `"regel"`).

**Mit den Urteilen: 30 Herausgeber, 45.236.224 Fundstellen — 79,9 %.**

## 4. Was die Messung nicht sagt

Sie sagt nicht, ob ein Herausgeber „gute" Datensätze führt. Sie misst eine einzige
Eigenschaft — wie oft sich Titel wiederholen — und die trennt Massenregistrierung von
Repositorium gut, aber nicht fehlerfrei. Wer auf der Liste steht, ist nicht
disqualifiziert: Einträge, die die **Sammlung** statt des Einzelstücks bezeichnen
(`granularitaet: collection` oder `series`), werden weiterhin aufgenommen.

Die Frage, ob ein Eintrag für diese Ökologie zählt, entscheidet diese Messung ohnehin
nicht — das tut Stufe 2 (Kernbestand).
