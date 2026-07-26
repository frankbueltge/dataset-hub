# Messprotokoll — <Quelle>

**Datum:** · **Skript:** `skripte/messe_<quelle>.py` · **Ergebnis-JSON:**
`ergebnisse/<datum>-<quelle>.json` · **Rohdaten:** `rohdaten/<...>.json.gz`

Jede Zahl in diesem Bericht stammt aus dem Ergebnis-JSON; jedes Ergebnis-JSON ist durch
committete Rohdaten gedeckt. Nichts wird geschätzt; Ausfälle stehen als Ausfälle da.

## 1. Zähler

Abfrage wörtlich + Ergebnis. Falls die Quelle keinen Zähler bietet: wie gezählt wurde
(Iteration, Kappe) und was das über den Wert aussagt.

## 2. Stichprobe

n, Ziehungsart (API-seitig zufällig / Convenience mit Begründung), Verzerrung ehrlich
benannt.

## 3. Feldabdeckung (auf der Stichprobe)

| Feld | Anteil belegt |
|---|---|
| Titel · Urheber · Herausgeber · Zugriffs-URL · Lizenz · Zeitraum · Räumlichkeit · Format | … |

## 4. Maschinenlesbarkeit

Format, Paginierung (Cursor? Deep-Paging-Limit?), Rate-Limits, Auffälligkeiten.

## 5. Inkrement-Fähigkeit

updated-since-Abfrage / OAI-PMH / Dump — mit Beleg (tatsächlich abgefragt), plus
Tagesvolumen falls messbar.

## 6. Gate-Bewertung → GO / NO-GO / GO mit Auflagen

## 7. Ausfälle und Anomalien

---

# Gates v0.1 (Änderung nur mit Begründung in `register.md`)

- **G1 — Inkrement-Weg belegt** (updated-since, OAI-PMH oder Dump): **Pflicht.** Ohne
  ihn keine fortlaufende Selbsterweiterung aus dieser Quelle.
- **G2 — Zugriffsweg wörtlich im Record:** ≥ 90 % der Stichprobe.
- **G3 — Titel ≥ 99 %** UND **(Urheber ODER Herausgeber) ≥ 80 %.**
- **G4 — Volliterierbarkeit:** Cursor/Dump ohne hartes Deep-Limit — sonst nur
  Inkrement-Betrieb ab Aufsetzzeitpunkt, mit dokumentierter Bestandslücke.

Lizenz-, Zeitraum- und Räumlichkeits-Abdeckung sind **informativ** (werden berichtet,
gaten nicht): sie bestimmen die Filterqualität des Hubs, nicht die Aufnahmefähigkeit
der Quelle. Ein NO-GO ist ein gültiges, bleibendes Messergebnis.
