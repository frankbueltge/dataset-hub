# Verfahrensnotizen — Messungen des Verfahrens gegen sich selbst

Was beim Bauen schiefging, mit Datum. Nach demselben Prinzip wie das
Ablehnungsregister: nicht stillschweigend korrigieren, sondern mitschreiben.

## 2026-07-26 — Commits haben fremde Arbeitsdateien eingesammelt

**Was passierte:** Während eine parallele Messsitzung (ArcGIS Hub, Kaggle) im selben
Arbeitsverzeichnis lief, wurden in der Hauptsitzung `git add -A` bzw. `git add
messungen/` ausgeführt. Dadurch landeten unfertige Dateien der Messsitzung in Commits
mit thematisch unpassenden Nachrichten:

- `8be62d8` („feat(schema): v0.2.0 …") enthält zusätzlich `messe_arcgis.py`,
  `messe_kaggle.py`
- `8bfc8b3` („docs: Snapshot-API-Vertrag …") enthält zusätzlich die
  ArcGIS-Ergebnis-JSON und drei Rohdatendateien

**Schaden:** Keine inhaltliche Verfälschung — der committete Stand stimmt mit den
finalen Dateien überein (per Diff geprüft). Der Schaden ist die unsaubere Historie:
Die Commit-Nachrichten beschreiben nicht, was die Commits enthalten.

**Nicht getan:** Historie umschreiben. Ein Force-Push auf bereits veröffentlichte
Commits ist destruktiv und würde die Spur des Fehlers tilgen — genau das, was dieses
Verzeichnis verhindern soll. Der Vermerk hier ist die Korrektur.

**Regel daraus:** In einem Arbeitsverzeichnis, in dem parallele Sitzungen laufen,
**nie `git add -A` oder Verzeichnis-weites `git add`** — nur explizite Pfadlisten der
Dateien, die zum jeweiligen Commit gehören.

## 2026-07-26 — Erster Auflösungslauf: 403 ist kein toter Link

53 von 200 Zugriffswegen antworteten mit HTTP 403, alle vom selben Host (GBIF).
Nachgeprüft statt vermutet: GBIF weist automatisierten Zugriff auf die Landing-Page
generell ab (auch mit Browser-Kennung), während seine API dieselbe Ressource mit 200
ausliefert. Der Datensatz existiert — nur die Prüfung ist verwehrt. Führte zur
Schema-Änderung v0.2.0 (`zugang.geprueft: versucht`), damit „geprüft, Host verweigert"
nicht wie „nie geprüft" aussieht.

## 2026-07-26 — Zenodo-Erstlauf scheiterte vollständig

Die erste Zenodo-Messung fragte mit `size=100` und erhielt dreimal HTTP 400 (anonymes
Limit ist 25, Rate-Limit 30/min). Die Messung fing es ab — ein Adapter hätte bei jedem
Lauf leer geliefert. Beleg dafür, dass Messen vor Bauen kommt.
