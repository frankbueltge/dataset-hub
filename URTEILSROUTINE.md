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
python3 pipeline/kandidaten.py --aus-snapshot
```

Die Saat ist ohne Angabe das heutige UTC-Datum. Der Aufruf ruft am Ende auch gleich alle
Zugriffswege ab (`pipeline/belege.py`, siehe unten) — **du selbst rufst keine URL per
`curl` auf**.

`--aus-snapshot` holt den **jüngsten veröffentlichten Bestand** — nicht einen lokalen Bau,
den es in deinem Checkout gar nicht gibt. Damit hängst du nicht daran, ob die nächtliche
Ernte pünktlich war (sie ist es oft nicht: GitHubs Zeitplan ist „best effort", am 27.07.
lief sie 3½ Stunden zu spät). Welchen Stand du beurteilt hast, steht in
`urteil/vorlage.json` unter `beurteilter_stand` — nenne ihn in der Commit-Nachricht.

Das erzeugt drei Dateien in `urteil/`:

| Datei | Inhalt |
|---|---|
| `kandidaten.jsonl` | Merge-Kandidaten: gleicher normalisierter Titel, gemeinsamer Urheber oder Herausgeber, noch nicht dieselbe Fassung. Je Paar beide Einträge vollständig mit Beleg |
| `stichprobe.jsonl` | Zufallsstichprobe automatisch aufgenommener Einträge (`status: ungeprueft`) |
| `vorlage.json` | Zähler des Laufs, inklusive **gekappter** Kandidaten |
| `belege.jsonl` | Je Zugriffsweg: HTTP-Status, finale URL, Inhaltstyp, Größe, Seitentitel, ob der registrierte Titel im Text steht; bei GBIF und ArcGIS zusätzlich die Antwort der öffentlichen API (`api`, `abgeleitet: true`) |

### Zugriffswege prüfen, ohne Freigabe

Die Routine läuft unbeaufsichtigt. Eigene Prüfungen per `curl` — Schleifen mit
Variablen, `curl … | python3`, `cd` vor git — lässt die Befehlsausführung **immer** von
einem Menschen freigeben, und dann hängt der Lauf (2026-11-06 und 2026-11-07, bis zu
zehn Rückfragen pro Lauf). Deshalb:

- Lies `urteil/belege.jsonl` mit dem Read-Werkzeug. Das ist der Beleg, den du nennst
  („Zugriffsweg 200, Seitentitel X, registrierter Titel im Text gefunden").
- Brauchst du eine weitere URL (etwa eine, auf die eine Seite weiterleitet), dann genau
  so, mit der URL wörtlich und ohne Variablen:
  `python3 pipeline/belege.py --url "https://…" --suche "Text, der dort stehen soll"`.
  Das Ergebnis wird an `urteil/belege.jsonl` angehängt.
- Wo der Text der Routine noch sagt, du sollst die Zugriffswege „per curl" aufrufen, ist
  seit 2026-11-07 dieser Weg gemeint.
- Steht `titel_im_text: false`, heißt das oft nur, dass die Seite ihren Inhalt per
  JavaScript nachlädt — dann zählt der `api`-Beleg oder der Seitentitel. Ein `status:
  null` ist ein Ausfall, kein Befund über die Ressource.

## Was zu tun ist

### 1. Merge-Kandidaten beurteilen

Je Paar entscheiden: **dasselbe Ding, verschiedene Fassungen desselben Werks, oder
verschiedene Dinge?** Maßgeblich ist das Identitätsmodell in `schema/SCHEMA.md`.

Belege prüfen, nicht Titel vergleichen. Nützlich sind: die abgerufenen Zugriffswege in
`urteil/belege.jsonl` vergleichen (wohin leiten sie weiter, welchen Titel zeigen sie), die Quell-IDs (aufeinanderfolgende DOIs deuten auf eine
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
python3 -m unittest discover -s pipeline/tests
```

Dann **nur das Journal** committen (`journal/entscheidungen.jsonl`, dazu ggf.
`messungen/VERFAHRENSNOTIZEN.md`) und pushen — explizite Pfade, nie `git add -A`. Jeder
Schritt ein eigener, kurzer Bash-Aufruf ohne `cd` davor: `git add journal/entscheidungen.jsonl`,
dann `git commit -m "…"`, dann `git push`.

**Du baust den Bestand nicht selbst.** Urteile sind Journal-Ereignisse; sie wirken beim
nächsten nächtlichen Bau, der sie anwendet. Das ist so gewollt: Dein Beitrag ist das
Urteil, nicht der Bau — und ein halb gebauter Bestand aus einer Urteilssitzung wäre
schlimmer als gar keiner.

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
