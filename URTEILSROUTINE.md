# Urteilsroutine

Der Auftrag der geplanten Claude-Code-Routine, die nachts nach der Ernte läuft.
Sie ist der einzige Schritt im Register, an dem ein Modell beteiligt ist — **und sie
läuft unter dem Abo, nie als API-Aufruf aus der Pipeline** (Bauregel: kein
API-Guthaben; ein Modellaufruf im Cron-Job auf fremder Infrastruktur bräuchte einen
eigenen Schlüssel).

Alles Deterministische bleibt außerhalb: Ernte, Normalisierung, Deduplizierung R1–R4,
Schranken, Bestandsbau. Die Routine bekommt fertige Vorlagen und gibt Urteile zurück.

## Ablauf

```bash
git pull
cd pipeline && python3 kandidaten.py --saat $(date -u +%Y%m%d)
```

Das erzeugt drei Dateien in `urteil/`:

| Datei | Inhalt |
|---|---|
| `kandidaten.jsonl` | Merge-Kandidaten: gleicher normalisierter Titel, gemeinsamer Urheber oder Herausgeber, noch nicht dieselbe Fassung. Je Paar beide Einträge vollständig mit Beleg |
| `stichprobe.jsonl` | Zufallsstichprobe automatisch aufgenommener Einträge (`status: ungeprueft`) |
| `vorlage.json` | Zähler des Laufs, inklusive **gekappter** Kandidaten |

## Was zu tun ist

### 1. Merge-Kandidaten beurteilen

Je Paar entscheiden: **dasselbe Ding, verschiedene Fassungen desselben Werks, oder
verschiedene Dinge?** Maßgeblich ist das Identitätsmodell in `schema/SCHEMA.md`.

Belege prüfen, nicht Titel vergleichen. Nützlich sind: die Zugriffswege tatsächlich
aufrufen und vergleichen, die Quell-IDs (aufeinanderfolgende DOIs deuten auf eine
Doppelablage oder eine mehrteilige Einreichung), Jahr und Herausgeber.

**Häufigster Fehlerfall, gemessen:** Serien sehen aus wie Dubletten. Herbarbelege
tragen als Titel den Artnamen, dazu denselben Herausgeber und Sammler — es sind aber
verschiedene physische Exemplare. Dasselbe gilt für Messreihen und Zeitscheiben.
**Im Zweifel `kein_merge`.** Eine unentdeckte Dublette ist ein Schönheitsfehler; eine
falsche Zusammenführung zerstört die Unterscheidung zwischen zwei realen Objekten.

Jedes Urteil wird an `journal/entscheidungen.jsonl` angehängt — auch das negative,
damit dieselbe Frage nicht monatlich neu gestellt wird:

```json
{"datum":"2026-07-27T06:00:00Z","typ":"merge","ebene":"werk",
 "mitglieder":["dh-...","dh-..."],
 "beleg":"Beide Zugriffswege lösen auf dieselbe Zenodo-Ablage auf; DOIs sind Version 1 und 2 derselben Einreichung.",
 "quelle":"urteilsroutine"}
{"datum":"2026-07-27T06:00:00Z","typ":"kein_merge",
 "mitglieder":["dh-...","dh-..."],
 "beleg":"Zwei Herbarbelege derselben Art, verschiedene Sammelnummern und Fundorte — keine Dublette.",
 "quelle":"urteilsroutine"}
```

`ebene` ist `fassung` (dasselbe Ding) oder `werk` (Fassungen desselben Werks).

### 2. Stichprobe sichten

Die gezogenen Einträge gegen ihre Quelle prüfen: Stimmt der Titel? Führt der
Zugriffsweg zum angekündigten Datensatz? Ist die Zuordnung plausibel?

- Alles in Ordnung → nichts tun (der Eintrag bleibt `ungeprueft`; die Routine ist eine
  Messung des Verfahrens, keine Einzelfreigabe).
- Etwas stimmt nicht → Ereignis `typ: "markiert"` mit Begründung ins Journal; im
  nächsten Bau erscheint der Eintrag entsprechend.
- Ein Muster fällt auf → in `messungen/VERFAHRENSNOTIZEN.md` festhalten. Wiederkehrende
  Muster gehören auf Dauer in eine deterministische Regel, nicht ins nächtliche Urteil.

### 3. Abschluss

```bash
cd pipeline && python3 baue_bestand.py && python3 -m unittest discover -s tests
cd ../oberflaeche && python3 generiere_index.py
```

Dann committen (nur explizite Pfade, nie `git add -A`) und pushen. Der Site-Build läuft
ohnehin um 03:50 UTC.

## Verbindliche Regeln

- **Nichts erfinden.** Ein Urteil ohne Beleg ist kein Urteil. Der Beleg nennt, was
  tatsächlich geprüft wurde — „beide URLs aufgerufen, führen auf dieselbe Seite", nicht
  „wirkt wie dasselbe".
- **Im Zweifel nicht zusammenführen.**
- **Rücknahme ist ein Revert.** Jedes Urteil ist ein Journal-Eintrag; ein falscher wird
  entfernt und neu gebaut. Deshalb kommt jedes Urteil in einen eigenen, beschreibenden
  Commit.
- **Keine KI-Produkt-Credits** in Commits.
- **Kappen sichtbar machen.** Sind Kandidaten gekappt worden (`vorlage.json`), gehört
  das in die Commit-Nachricht — sonst sieht ein abgearbeiteter Stapel wie ein leerer aus.
