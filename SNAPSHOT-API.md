# Snapshot-API — der Vertrag für Pipelines

Die research ecology fragt den Hub **nicht über einen Dienst** ab, sondern über
versionierte Snapshots. Kein Server, keine Verfügbarkeitsabhängigkeit, keine zweite
Wahrheit: Oberfläche und Pipelines lesen denselben Bestand.

## Vertrag

1. **Auffinden:** jüngstes GitHub-Release mit Tag `snapshot-YYYY-MM-DD` im Repo
   `frankbueltge/dataset-hub`.
2. **Prüfen:** `snapshots/<tag>.manifest.json` (in Git) nennt `schema_version` und
   SHA-256 jedes Assets. **Prüfsumme vergleichen, Major-Version pinnen.** Weicht die
   Major-Version ab, bricht die Pipeline ab, statt still Falsches zu lesen.
3. **Lesen:** `hub-<datum>.sqlite.gz` entpacken, lokal per SQL abfragen.

```python
import json, sqlite3, urllib.request, gzip, hashlib

MAJOR_ERWARTET = 0  # bricht bei brechenden Schemaänderungen ab
# Release-Assets über die GitHub-API auflösen; URLs nie konstruieren.
```

## Tabellen

| Tabelle | Inhalt |
|---|---|
| `eintraege` | ein Zeile je Eintrag; Spalte `json` enthält den vollständigen Eintrag nach `schema/eintrag.schema.json` |
| `eintraege_fts` | FTS5-Volltext über Titel und Beschreibung (`MATCH`) |
| `relationen` | quellen-behauptete Beziehungen (`IsVersionOf` u. a.) |
| `fundstellen` | Herkunft je Ernte |
| `ablehnungen`, `ausfaelle` | Verworfenes mit Grund; Quellausfälle |
| `meta` | `schema_version`, Bauzeit, Zähler |

## Drei Regeln beim Lesen

- **Leer heißt „Quelle sagt nichts", nicht „gibt es nicht".** Nie mit Vermutungen füllen.
- **`zugang_geprueft` ehrlich auswerten:** `landing`/`download` = bestätigt ·
  `versucht` = geprüft, aber Host antwortete nicht mit 2xx (403 ist meist Bot-Schutz,
  kein toter Link — `zugang_http_status` sagt es) · `none` = ungeprüft.
  `status = 'ungeprueft'` heißt: automatisch aufgenommen, nicht inhaltlich geprüft.
- **Vollständigkeit ist beziffert, nicht behauptet.** `quellfenster` im Manifest sagt,
  welcher Zeitraum je Quelle geerntet wurde und ob der Lauf vollständig war.
  Der Hub erntet ab Aufsetzzeitpunkt vorwärts; der Altbestand fehlt, bis der
  Bulk-Bootstrap läuft.

## Beispiel

```sql
-- Offen lizenzierte Datensätze mit bestätigtem Zugriffsweg, Volltextsuche
SELECT e.titel, e.zugang_url, e.lizenz_id
FROM eintraege e
JOIN eintraege_fts f ON f.id = e.id
WHERE f.eintraege_fts MATCH 'temperature'
  AND e.lizenz_id LIKE 'cc%'
  AND e.zugang_geprueft IN ('landing', 'download')
LIMIT 50;

-- Werke mit mehreren Fassungen (Dedup-Ergebnis)
SELECT werk_id, COUNT(*) fassungen FROM eintraege
GROUP BY werk_id HAVING fassungen > 1 ORDER BY fassungen DESC;
```
