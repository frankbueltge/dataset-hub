# Messprotokoll — HuggingFace Datasets

**Datum:** 2026-07-26 · **Skript:** `skripte/messe_huggingface.py` · **Ergebnis-JSON:**
`ergebnisse/2026-07-26-huggingface.json` · **Rohdaten:** `rohdaten/huggingface-stichprobe.json.gz`

## 1. Zähler

**Kein Zähler vorhanden** (kein `X-Total-Count` in der Antwort). Zähl-Iteration über
den Link-Header-Cursor: 120 Seiten à 1.000 = **120.000 gezählt, Iteration bei der
Kappe gestoppt — der tatsächliche Bestand ist GRÖSSER**. Cursor-Volliteration ist
damit zugleich belegt.

## 2. Stichprobe

n = 200, Convenience: erste 200 der Standardsortierung mit `full=true` —
**nicht gleichverteilt** (Standardsortierung bevorzugt populäre/aktive Datasets).

## 3. Feldabdeckung

| Feld | Anteil belegt |
|---|---|
| id (technischer Name) | 100 % |
| Autor im Namensraum (`org/name`) | 100 % |
| Anzeigename (cardData.pretty_name) | 62,5 % |
| Lizenz (Tag oder cardData) | 81,5 % |
| Beschreibung | 98 % |
| lastModified / createdAt | 100 % |
| **explizites URL-Feld** | **0 %** |
| Download-Zähler | 100 % |

`gated`-Verteilung: False 165 / auto 28 / manual 7 — die Zugangsstufe des Designs
(open / registration / request) ist **direkt ablesbar**.

## 4. Maschinenlesbarkeit

JSON, sauber; Cursor via Link-Header. Auch der **Detail-Endpunkt je Dataset führt
kein URL-Feld** (Schlüssel: _id, author, cardData, createdAt, description, disabled,
downloads, gated, id, lastModified, likes, private, sha, siblings, usedStorage).

## 5. Inkrement-Fähigkeit

`sort=lastModified&direction=-1` ✓ (HTTP 200, frischester Wert vom Messtag).

## 6. Gate-Bewertung → **ENTSCHEIDUNG ERFORDERLICH (Frank)**

G1 ✓ · G3 ✓ (id 100 %) · G4 ✓ (Cursor belegt) · **G2 ✗: 0 % wörtliche Zugriffs-URL.**
Die Quelle liefert nirgends eine URL — jeder Zugriffsweg müsste aus der id nach dem
dokumentierten Adressschema des Hubs gebildet werden. Das kollidiert frontal mit der
Bauregel „Nie URLs konstruieren".

Optionen: **(a)** dokumentierte, eng begrenzte Ausnahme — Zugriffsweg aus dem
publizierten API-Vertrag der Quelle, zusätzlich **Pflicht-Auflösung (HTTP) vor jeder
Aufnahme**, Ausnahme im Design vermerkt; **(b)** NO-GO. Keine Aufnahme vor dieser
Entscheidung.

## 7. Ausfälle und Anomalien

Keine. 122 Abfragen der Zähl-Iteration alle HTTP 200.
