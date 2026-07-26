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

## 2026-07-26 — „Im Archiv behalten" war keine Ausnahme vom Speichern (Kaggle)

Nach dem Rückzug der Kaggle-Einträge hieß es hier zunächst: aus dem Bestand genommen,
**Rohernte bleibt im Archiv**. Frank hat den Widerspruch benannt: Wenn die Bedingungen
das Speichern wesentlicher Teile untersagen, ist auch das Archiv Speichern — und unser
Archiv liegt öffentlich auf GitHub. Die Rohernten waren als Release-Dateien sogar
selbst veröffentlicht.

Der Befund war zutreffend. Kaggle-Inhalte lagen an drei Stellen öffentlich:
zwei Roherntedateien im Release, 9.991 Ablehnungszeilen mit Kennungen und 10.056
Fundstellen-Zeilen im Snapshot.

**Gelöscht:** die beiden Roherntedateien (Release und lokal); die Kennungen aus
Ablehnungs- und Fundstellen-Tabelle.

**Behalten:** die Ernte-Manifeste (Lauf, Zeitpunkt, Anzahl, Prüfsumme) und ein
Sammeleintrag im Ablehnungsregister. Das ist **unsere Buchführung über unser eigenes
Handeln**, kein Fremdinhalt — und genau der Teil, der die Nachprüfbarkeit trägt.

**Bewusster Eingriff in ein append-only-Register**, hier begründet: Die
Unantastbarkeit schützt davor, Geschichte stillschweigend hübscher zu machen. Hier
wurde Material Dritter entfernt, das wir nicht speichern dürfen, und durch einen
Eintrag ersetzt, der den Vorgang *vollständiger* beschreibt als 9.991 gleichlautende
Zeilen. Der Eingriff steht im Git-Verlauf und hier.

**Offen und ehrlich vermerkt:** Der Git-Verlauf des Repos enthält die früheren
Fassungen des Ablehnungsregisters mit den Einzelkennungen. Sie zu tilgen hieße,
die Historie umzuschreiben — verhältnismäßig wäre das nur, wenn es um mehr ginge als
um eine Liste von Kennungen. Falls das gewünscht wird, ist es eine eigene Entscheidung.

**Regel daraus:** „Wir veröffentlichen es nicht, wir behalten es nur" ist keine
Rechtsposition. Wo Speichern untersagt ist, ist Speichern untersagt — auch still.

## 2026-07-26 — Die Convenience-Stichprobe hat eine Lücke verdeckt (ArcGIS)

Das Messprotokoll ArcGIS wies **100 % Zugriffs-URL** aus (n=200, zwei Seiten der
Standardsortierung). Im ersten größeren Erntelauf (6.000 Fundstellen → 4.434 Einträge)
scheiterten **137 Einträge an der Schranke `keine-zugangs-url`** — rund 3 %.

Kein Widerspruch, sondern die vorhergesagte Schwäche: Die Stichprobe war ausdrücklich
als Convenience-Ziehung markiert („kein Zufallsparameter in der API bekannt"), und
genau solche Ziehungen unterschätzen seltene Ausfälle. Die Schranke hat gehalten und
das Fehlende sichtbar ins Ablehnungsregister geschrieben, statt es durchzulassen.

**Regel daraus:** Eine Feldabdeckung aus einer Convenience-Stichprobe ist eine
Untergrenze für Probleme, keine Zusage. Deckungswerte von 100 % aus solchen Ziehungen
werden im Register künftig als „100 % in der Stichprobe (Convenience — Ausreißer
möglich)" geführt, nicht als Eigenschaft der Quelle.

## 2026-07-26 — HEAD ist kein Befund über die Ressource (400 falsche Negative)

Nach der ersten großen Kaggle-Ernte meldete der Auflösungslauf **0 von 400 erfolgreich**
— zuvor waren es 144 von 200 gewesen. Der Sprung war das Alarmsignal.

Ursache: `aufloese.py` prüfte mit HTTP HEAD und wich nur bei 405/403/501 auf GET aus.
**Kaggle antwortet auf HEAD mit 404 und auf GET mit 200** (nachgemessen an derselben
URL). Alle 400 Einträge waren erreichbar und wurden trotzdem als „geprüft, nicht
bestätigt (404)" vermerkt — genau das falsche Negativ, das im Bestand später wie
Link-Rot ausgesehen hätte.

Behoben: **Jedem Nicht-2xx aus HEAD wird jetzt mit GET nachgegangen.** Ein
HEAD-Fehlschlag ist ein Befund über die Methode, nicht über die Ressource. Nach der
Korrektur: 450 von 450 bestätigt.

Zusätzlich: `aufloese.py --wiederholen` versucht gescheiterte Prüfungen erneut
(bestätigte bleiben unangetastet). Das Protokoll bleibt append-only — ein neuer
Eintrag überschreibt den alten nicht, sondern löst ihn ab; `baue_bestand.py` nimmt
je Eintrag den letzten Stand.

**Regel daraus:** Ein plötzlicher Sprung in einer Erfolgsquote ist zuerst ein Verdacht
gegen das eigene Messverfahren, nicht gegen die Welt.

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
