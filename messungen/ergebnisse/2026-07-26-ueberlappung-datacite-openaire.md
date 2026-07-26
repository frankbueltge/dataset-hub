# Messprotokoll — Überlappung DataCite ↔ OpenAIRE

**Datum:** 2026-07-26 · **Skript:** `skripte/ueberlappung_datacite_openaire.py` ·
**Ergebnis-JSON:** `ergebnisse/2026-07-26-ueberlappung-datacite-openaire.json` ·
**Eingabe:** die 200 DOIs der committeten DataCite-Zufallsstichprobe (keine neue Ziehung)

## Verfahren

Jeder DOI der DataCite-Stichprobe wurde einzeln gegen
`api.openaire.eu/search/datasets?doi=<doi>` geprüft (gedrosselt, 1,2 s). Da die
DataCite-Stichprobe API-seitig zufällig gezogen wurde, ist das Ergebnis eine
belastbare Schätzung der Richtung DataCite→OpenAIRE.

## Ergebnis

| | |
|---|---|
| DOIs geprüft | 200 / 200 |
| in OpenAIRE gefunden | **199** |
| HTTP-Fehler / Ausfälle | 0 / 0 |
| **Anteil** | **99,5 %** |

## Konsequenz für die Quellenstrategie

OpenAIRE enthält den DataCite-Datensatzbestand praktisch vollständig. Die
Zähler-Differenz (106,1 Mio. − 72,7 Mio. ≈ 33,5 Mio. Fundstellen) ist der einzige
Anteil, den OpenAIRE zusätzlich trägt — großteils OAI-aggregierte Records ohne DOI.
**Der Kern wird über DataCite geerntet; OpenAIRE wird erst nachvermessen (Graph-API),
wenn der DataCite-Kern steht.** Ein paralleler Doppel-Harvest von 72 Mio. redundanten
Fundstellen wäre reine Dedup-Last ohne Informationsgewinn.
