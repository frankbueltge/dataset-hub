# Bilanz der Neufassung — was der Filter aus dem Register gemacht hat

**Datum:** 2026-07-27 · **Grundlage:** `fundstellen/manifeste/steinbruch-20260727T105225Z.json`,
`bestand/hub.sqlite` (meta-Tabelle), `register/ablehnungen.jsonl` ·
**Entscheidung:** frankbueltge.de → `docs/design/2026-07-27-register-neufassung.md`

## 1. Der Steinbruch

56.620.404 Datensätze des DataCite Public Data File gelesen, **0 kaputte Zeilen**.

| | Anzahl | Anteil |
|---|---:|---:|
| Massenregistrierung abgewiesen | 45.225.488 | 79,9 % |
| ohne benannte Lizenz abgewiesen | 6.761.799 | 11,9 % |
| Grenzfälle gesehen, **im Steinbruch gelassen** | 252.311 | 0,4 % |
| **genommen** (Kernbestand per Regel) | **16.443** | 0,03 % |

Die 252.311 Grenzfälle sind eine **bewusste Kappung**: Der Abbau nimmt nur, was der Sieb
per Regel entscheidet. Ein Urteilsvorrat dieser Größe wird nie abgearbeitet, und die
Einträge blähten den Bestand um das Fünfzehnfache auf, ohne je sichtbar zu werden. Wer
sie will: `hole_aus_steinbruch.py --auch-grenzfaelle`.

## 2. Der Bestand

| | vorher (26.07.) | nachher (27.07.) |
|---|---:|---:|
| Einträge | 17.327 | 19.502 |
| Werke | 16.445 | 10.781 |
| davon Kernbestand (= Seiten auf der Website) | — | 16.494 |
| offene Grenzfälle (warten auf ein Urteil) | — | 365 |

Aus den **alten** Ernten überlebten 3.060 von 17.327 Einträgen. Abgelehnt wurden 14.267:

| Grund | Anzahl |
|---|---:|
| `massenregistrierung` | 10.736 |
| `lizenz-nicht-benannt` | 3.531 |

Jede Ablehnung steht mit Grund in `register/ablehnungen.jsonl`. Der Rest des heutigen
Bestands (16.443 Einträge) kommt aus dem Steinbruch.

## 3. Zwei Befunde, die nicht schön sind

**Der Prüfstand ist fast ungedeckt.** 57 Einträge im Bestand haben eine bestätigte
HTTP-Auflösung, davon liegen **2 im Kernbestand** — 0,01 % der Seiten. Der beanspruchte
Mehrwert „geprüft statt behauptet" (Neufassung §2) ist damit im Moment eine Absicht,
keine Eigenschaft. Die Registerseite sagt das jetzt im Kopf, statt den Anspruch zu
behaupten. Der Kernbestand ist klein genug, dass sich das einlösen lässt — 16.494
gedrosselte HTTP-Abrufe sind machbar; 17.327 waren es nie.

**Die Zweistufigkeit ist praktisch eingeebnet.** 16.494 von 19.502 Einträgen (84,6 %)
sind Kernbestand — nicht weil der Sieb großzügig wäre, sondern weil der Abbau
konstruktionsbedingt nur Regel-Treffer holt. Der „breite Bestand", den die Praxen
abfragen sollten, ist derzeit fast identisch mit der kuratierten Auswahl. Das ist kein
Fehler, aber es heißt: die Breite muss aus **anderen Quellen** kommen
(Regierungsportale, kuratierte Listen), nicht aus mehr DataCite.

## 4. Was die Zahlen nicht sagen

Sie sagen nichts über die Qualität der Auswahl. Der Sieb entscheidet an Begriffen im
Titel; er trifft „OSE-Instruct: Open-Source Ecosystem Instruction Tuning Dataset" und
„China's Climate Policy Inventory" ebenso wie Fehlgriffe, die niemand gezählt hat. Eine
Stichprobe des Kernbestands gegen das Kriterium steht aus — sie gehört in die
Urteilsroutine, nicht in eine Messung.
