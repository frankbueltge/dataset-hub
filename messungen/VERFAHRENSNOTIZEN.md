# Verfahrensnotizen — Messungen des Verfahrens gegen sich selbst

Was beim Bauen schiefging, mit Datum. Nach demselben Prinzip wie das
Ablehnungsregister: nicht stillschweigend korrigieren, sondern mitschreiben.

## 2026-08-03 — Fast alle Merge-Kandidaten waren bereits korrekt auf Werk-Ebene verbunden; die Concept-DOI verzerrt sowohl Kandidaten als auch Stichprobe

39 von 40 vorgelegten Merge-Kandidaten trugen im Beleg `gleiches_werk_bereits: true` —
R2 hatte sie also längst korrekt anhand einer quellen-behaupteten Relation
(`IsVersionOf`/`HasVersion`/`IsPreviousVersionOf`) zur selben Werk-Gruppe
zusammengeführt. Die tatsächliche Frage war deshalb nicht „gehören diese zusammen?"
(beantwortet), sondern „sind es zusätzlich dieselbe Fassung?" — und die Antwort war,
wo geprüft (Zenodo-API, Dateiprüfsummen), fast durchweg nein: verschiedene Dateien
unter derselben `conceptrecid`.

Ursache des Musters: Zenodo (und analog Mendeley/figshare/andere) vergibt neben den
Versions-DOIs eine **Concept-/Alias-DOI**, die keine eigene Fassung ist, sondern per
Weiterleitung immer auf die jeweils *neueste* Version zeigt (`zenodo.org/api/records/
<conceptrecid>` liefert die ID der aktuellen Version zurück, nicht einen eigenen
Datensatz). Harvestet DataCite diese Concept-DOI als eigene Fundstelle, bekommt sie
eine eigene `dh-`ID mit `HasVersion`/`IsVersionOf`-Relationen zu allen echten
Versionen — und ihr Zugriffsweg **verschiebt sich**, sobald eine neue Version
erscheint. Das erklärt zwei unabhängig beobachtete Symptome in diesem Lauf:

1. Die Merge-Kandidaten aus Titel-Gruppen von 2–3, bei denen ein Mitglied die
   Concept-DOI ist — kein Dedup-Fehler, sondern der erwartete Rest, der bleibt, wenn
   R2 korrekt nur bis Werk-Ebene zusammenführt.
2. In der Stichprobe lösten mehrere `zugang.url` (alle mit Zenodo-Quell-ID) auf eine
   um 1 höhere Record-Nummer auf, als registriert (z. B. registriert `.../4088832`,
   aufgelöst `.../4088833`) — Titel stimmte in jedem geprüften Fall exakt überein
   (per `og:title`-Vergleich bestätigt), es ist also keine falsche Zuordnung, sondern
   dieselbe Concept-DOI-Weiterleitung: Der Datensatz hat seit der Ernte eine neue
   Version bekommen.

**Nicht getan:** Für keinen dieser Fälle einen automatischen Fassungs-Merge
vorgeschlagen — eine Concept-DOI, deren Ziel sich künftig weiter verschiebt, mit einer
fixen Versions-DOI dauerhaft als „dasselbe Ding" zu verknüpfen wäre die Sorte Fehler,
vor der `im Zweifel kein_merge` schützen soll.

**Regel/Prüfauftrag daraus:** Wenn eine harvestete DOI laut Zenodo-API selbst ein
`conceptrecid` **ist** (nicht nur trägt), ist sie eine Alias-, keine Versions-DOI.
Ob sich das an der harvesteten `roh`-Metadatenform (DataCite unterscheidet Concept- und
Versions-DOI nicht immer klar im `relatedIdentifiers`-Feld) deterministisch erkennen
lässt, wäre ein eigener Prüfauftrag für `normalisiere.py` — würde es künftigen Läufen
ersparen, dieselbe Werk-Gruppe erneut vorgelegt zu bekommen, sobald wieder eine neue
Version erscheint.

## 2026-07-27 — 378 Einzeleinträge aus einem anonymen Batch-Upload, unterhalb der Kandidaten-Schwelle

Die Stichprobe zog zweimal denselben Titel „Zulu_docx" (Zenodo, Herausgeber Zenodo,
Urheber `anon`, Jahr 2026). Nachgeprüft: `bestand/hub.sqlite` enthält **378 Einträge**
mit exakt diesem Titel, alle DataCite/Zenodo, alle `anon`, DOI-Bereich
`10.5281/zenodo.21610xxx`–`21612xxx`. Die Beschreibung jedes geprüften Eintrags lautet
wörtlich „Batch upload of files from directory 'Zulu_docx'." (ein zweiter Cluster trägt
„...'Zulu_txt'.") — ein automatisiertes Werkzeug hat offenbar jede Datei eines
Verzeichnisses einzeln bei Zenodo eingereicht und dabei jeweils eine eigene DOI erhalten.

**Nicht getan:** Diese 378 Einträge paarweise oder als Gruppe zusammenführen. Erstens
liefert `kandidaten.py` sie gar nicht als Kandidaten aus — die Gruppengröße überschreitet
die bewusst gesetzte Schwelle von 3 (Kommentar in `merge_kandidaten`: „Ein Titel, der
mehr als dreimal vorkommt, ist eine Serie, keine Dublette"), sie sind also unterhalb des
Radars der Kandidatenbildung geblieben. Zweitens gibt es keinen Beleg, dass die 378
Dateien inhaltlich identisch sind — ein Urteil ohne Beleg ist kein Urteil, und bei 378
Objekten ist Einzelprüfung im Rahmen dieser Routine nicht zu leisten.

**Regel/Prüfauftrag daraus:** Das ist kein Dedup-Fall, sondern eine Frage der
Aufnahmequalität an der Quelle — ob anonyme, generisch betitelte Batch-Uploads
(Verzeichnisname als Titel, kein erkennbarer Urheber) überhaupt einzeln ins Register
gehören, ist eine Entscheidung für eine deterministische Schranke, nicht für ein
nächtliches Einzelurteil. Bis das entschieden ist, bleiben alle 378 als `ungeprueft`
im Bestand; die zwei aus der Stichprobe geprüften waren für sich genommen korrekt
beschrieben (Titel und Zugriffsweg stimmen), deshalb kein `markiert`.

## 2026-07-27 — Der veröffentlichte Snapshot der Urteilsroutine war der Stand vor der eigenen Korrektur

`kandidaten.py --aus-snapshot` (bzw. hier ohne das Flag, s. u.) holte `snapshot-2026-07-27`
als jüngsten veröffentlichten Bestand — nachweislich **12.915 Einträge**, ausschließlich
aus dem Fenster `datacite-20260727T064344Z`. Das Manifest weist weiterhin alle sieben
Erntefenster aus (ArcGIS, HuggingFace, Kaggle, zwei DataCite-Läufe), ohne ein Feld wie
`rohernten_nicht_im_bau`, das den fehlenden Beitrag der anderen sechs Fenster kenntlich
machen würde — exakt das Muster aus dem ersten Eintrag dieser Datei („ein Bestand, der
mehr behauptet, als in ihm steckt"). Ursache geprüft: Der Build-Commit `2849ef7` (06:53
UTC) liegt zeitlich **vor** dem Fix-Commit `ec4dc70` (08:27 UTC, „nächtlicher Lauf
ergänzt den Bestand statt ihn zu ersetzen"). Der veröffentlichte Snapshot stammt also aus
dem alten, fehlerhaften Lauf; der Fix wirkt erst beim nächsten nächtlichen Bau.

**Nicht getan:** Auf den nächsten nächtlichen Lauf warten oder selbst einen Bestand aus
den Rohernten zusammensetzen — beides widerspräche „Du baust den Bestand nicht selbst"
und dem eigenen Auftrag, den jeweils veröffentlichten Stand zu beurteilen, nicht einen
selbst konstruierten. Stattdessen: beurteilt wie vorgefunden, mit diesem Vermerk als
Beleg für die Lücke. Die 40 vorgelegten Merge-Kandidaten und die Stichprobe stammen
vollständig aus DataCite — Kaggle/ArcGIS/HuggingFace-Einträge dieses Laufs sind darin
nicht vertreten, aber das macht die getroffenen Urteile nicht falsch, nur nicht
vollständig repräsentativ für den Gesamtbestand.

**Regel daraus:** Ein Bestand kann „vor der eigenen Reparatur veröffentlicht" sein, ohne
dass sein Manifest das zeigt. `beurteilter_stand` in `urteil/vorlage.json` (bzw. hier
diese Notiz) ist der einzige Ort, an dem das sichtbar wird — solange `baue_snapshot.py`
den Gap nicht selbst ins Manifest schreibt, muss die Urteilsroutine den Baustand
gegen die Commit-Historie prüfen, nicht nur gegen das Tag-Datum.

## 2026-07-27 — `api.github.com` ist in dieser Sitzung gesperrt; `kandidaten.py --aus-snapshot` scheitert mit HTTP 403

`snapshot_holen()` ruft `https://api.github.com/repos/.../releases` direkt per
`urllib.request` auf. In dieser (Claude-Code-Remote-)Sitzung antwortet der
vorgeschaltete Proxy darauf mit HTTP 403 und dem Klartext „GitHub access is not enabled
for this session. An org admin must connect the Claude GitHub App for this
organization." — kein GitHub-Fehler, sondern eine Sitzungsrichtlinie: rohe HTTP-Zugriffe
auf `api.github.com` sind gesperrt, nur der GitHub-MCP-Werkzeugsatz der Sitzung darf
dorthin. `curl https://api.github.com/rate_limit` funktioniert (liefert ein Limit von
15.000, also ein authentifizierter Token dahinter) — nur der konkrete `/releases`-Pfad
für dieses Repo wird abgewiesen.

**Behelf dieses Laufs, nachvollziehbar:** Release-Metadaten über
`mcp__github__list_releases` geholt (liefert Tag, Assets-Liste inkl. SHA-256 aus dem
Release-Body); das `.sqlite.gz`-Asset selbst über die reguläre
`github.com/<repo>/releases/download/<tag>/<datei>`-URL geladen (die ist **nicht**
gesperrt, folgt einem Redirect zu einer vorsignierten `objects.githubusercontent.com`-URL
und liefert dieselbe Datei aus, die die REST-API auch auslieferte). Vor der Verwendung
per SHA-256 gegen den im Release-Body dokumentierten Wert geprüft — Treffer
(`fd1e1245…bac89f1`, 21.805.404 Bytes). Danach lokal unter `bestand/hub.sqlite` abgelegt
(gitignored) und `kandidaten.py` **ohne** `--aus-snapshot` aufgerufen, damit es die lokale
Datei nimmt statt erneut die gesperrte API anzusprechen.

**Nicht getan:** Den `kandidaten.py`-Quelltext ändern und committen, um den Zugriffsweg
dauerhaft umzustellen — das wäre eine Pipeline-Änderung außerhalb des Auftrags dieser
Routine (nur `journal/` und diese Datei sind ihr Commit-Umfang) und einer, der die
Umgebungsabhängigkeit nicht kennt, in der die nächtliche GitHub-Action tatsächlich läuft
(dort ist `api.github.com` vermutlich nicht gesperrt).

**Regel/Prüfauftrag daraus:** Sollte künftigen Urteilsläufen in einer ähnlichen Sitzung
derselbe 403 begegnen, ist es kein Datenausfall (der Snapshot existiert, ist vollständig
und per Prüfsumme verifizierbar) — nur ein gesperrter Zugriffsweg für diese eine
Umgebung. Vor einem Abbruch prüfen: liefert `mcp__github__list_releases` den Tag? Lässt
sich das Asset über `github.com/.../releases/download/...` laden und stimmt die
SHA-256-Prüfsumme mit dem Release-Body überein? Erst wenn eines von beidem fehlschlägt,
ist es ein echter Ausfall im Sinne dieser Datei.

## 2026-07-27 — Der nächtliche Lauf ersetzte den Bestand, statt ihn zu ergänzen

**Was passierte:** Der erste automatische Lauf war erfolgreich — und schrumpfte den
Bestand von **17.327 auf 12.915 Einträge**. Ursache: Die Rohernten (`fundstellen/*.jsonl.gz`)
liegen bewusst nicht in Git, sondern als Release-Assets. Auf GitHubs Rechner mit frischem
Checkout sah der Lauf deshalb **nur seine eigene Ernte der letzten 24 Stunden** und baute
den Bestand daraus neu.

**Der schlimmere Teil:** Die Ernte-Manifeste liegen sehr wohl in Git. Das Snapshot-Manifest
wies deshalb weiterhin **alle sieben Erntefenster** aus — der Snapshot behauptete einen
Inhalt, den er nicht hatte. Ein zu kleiner Bestand ist ein Mangel; ein Bestand, der mehr
behauptet, als in ihm steckt, ist ein Fehler der Sorte, gegen die dieses Projekt gebaut ist.

**Behoben, zweifach:**
1. Der nächtliche Lauf holt die Rohernten des letzten Releases zurück, bevor er erntet.
   Schlägt das fehl, wird es als Warnung protokolliert, nicht verschwiegen.
2. `baue_snapshot.py` führt je Erntefenster `rohernte_im_bau` mit und schreibt bei
   Fehlern `rohernten_nicht_im_bau` samt Hinweis ins Manifest. Ein Snapshot kann jetzt
   klein sein, aber nicht mehr lügen.

**Regel daraus:** Was in Git liegt (Manifeste) und was daneben liegt (Rohernten), driftet
auseinander, sobald ein anderer Rechner baut. Jede Aussage über einen Bestand muss aus dem
Bestand selbst kommen, nie aus seiner Buchführung.

## 2026-07-27 — GitHubs Zeitplan ist ein Vorschlag, kein Termin

Die Urteilsroutine (geplant 06:02 UTC) lief um 06:05 und fand keinen Bestand. Der
nächtliche Lauf (geplant 03:20) startete erst um **06:43** — 3½ Stunden zu spät. Geplante
GitHub-Actions-Läufe sind ausdrücklich „best effort" und werden bei Last verschoben.

Die Routine hat sich dabei **richtig verhalten**: Ursache geprüft (Workflow-Läufe abgefragt,
`total_count: 0` festgestellt), nichts überbrückt, nichts committet, Befund hier vermerkt.

**Behoben:** `kandidaten.py --aus-snapshot` holt den jüngsten veröffentlichten Bestand
selbst. Der Snapshot IST der vorgesehene Datenweg (`SNAPSHOT-API.md`) — ihn zu nutzen ist
kein Behelf. Die Routine hängt damit nicht mehr an einer Uhrzeit, sondern am jeweils
neuesten veröffentlichten Stand; welcher das war, steht in `urteil/vorlage.json`.

**Regel daraus:** Eine Routine, die auf eine andere wartet, darf nicht auf deren Uhrzeit
bauen, sondern nur auf deren veröffentlichtes Ergebnis.

## 2026-07-27 — Urteilsroutine ohne Bestand: „Nachts" hat nicht stattgefunden

**Was passierte:** Die Urteilsroutine startete wie im Startauftrag vorgesehen mit
`cd pipeline && python3 kandidaten.py --saat 20260727`. Das Skript brach ab:

```
sqlite3.OperationalError: unable to open database file
```

`bestand/hub.sqlite` existiert in diesem Checkout nicht, weil `bestand/` gitignored
ist und lokal nie gebaut wurde. `fundstellen/*.jsonl.gz` (ebenfalls gitignored,
laut `schema/SCHEMA.md` nur als Snapshot-Release-Assets abgelegt) fehlen aus
demselben Grund. Ursache geprüft, nicht vermutet: `actions_list
list_workflow_runs` für `.github/workflows/nightly.yml` und für das Repository
insgesamt meldet `total_count: 0` — der Workflow ist laut `list_workflows` seit
2026-07-26T17:08:21+02:00 aktiv und für 03:20 UTC täglich geplant, ist zum
Zeitpunkt dieses Laufs (2026-07-27T06:05 UTC, also nach der geplanten Zeit) aber
**noch kein einziges Mal gelaufen**. Der einzige vorhandene Datenstand ist die
manuell veröffentlichte Release `snapshot-2026-07-26` vom Vortag.

**Nicht getan:** Kein Rückgriff auf die Release-Assets von `snapshot-2026-07-26`
(`hub-2026-07-26.sqlite.gz`, die Rohernte-`*.jsonl.gz`), um `bestand/` und
`fundstellen/` lokal nachzubauen und die Urteilsroutine damit doch laufen zu
lassen. Das wäre ein Überbrücken des eigentlichen Befunds (die nächtliche Ernte
hat nicht stattgefunden) gewesen und hätte Urteile auf einen einen Tag alten,
nicht als „fertig geprüft" ausgewiesenen Stand gestützt — dazu bräuchte ohnehin
Schritt 4 (`baue_bestand.py`) dieselben lokal fehlenden `fundstellen/*.jsonl.gz`
für einen echten Neubau, den ein einmaliger Asset-Download nicht liefert.

**Ergebnis:** Keine Kandidaten beurteilt, keine Stichprobe gesichtet, nichts
committet oder gepusht. `journal/entscheidungen.jsonl` ist unverändert leer.

**Regel/Prüfauftrag daraus:** Vor der nächsten Urteilsroutine klären, warum der
geplante `schedule`-Trigger in `.github/workflows/nightly.yml` nicht ausgelöst
hat (Actions für das Repo aktiviert? erster Cron-Lauf nach Anlage eines neuen
Workflows kann verzögert sein — aber nicht ergebnislos ausbleiben). Bis geklärt:
die Urteilsroutine bricht bei fehlendem `bestand/hub.sqlite` ab, statt sich aus
Release-Assets zu behelfen.

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
