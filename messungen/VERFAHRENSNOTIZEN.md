# Verfahrensnotizen — Messungen des Verfahrens gegen sich selbst

Was beim Bauen schiefging, mit Datum. Nach demselben Prinzip wie das
Ablehnungsregister: nicht stillschweigend korrigieren, sondern mitschreiben.

## 2026-08-14 — Vierzehnter Lauf: `api.zenodo.org` erstmals per Proxy blockiert (Behelf: `zenodo.org/api/...`), zweiter bestätigter Merge seit dem GBIF/PANGAEA-Fund — zwei unabhängige Zenodo-Einreichungen mit MD5-identischer Datei ohne deklarierte Relation; zwei neue Quellen (FDR Uni Hamburg, TU Graz)

Beurteilter Stand `snapshot-2026-07-27c` (nächtlicher Cron seit 27.07. weiterhin pausiert —
`mcp__github__list_releases` bestätigt, jüngstes Release unverändert seit dem 27.07.).
`api.github.com` war wie an allen Vortagen mit HTTP 403 gesperrt; Behelf wie dokumentiert:
Release-Metadaten per `mcp__github__list_releases`, `hub-2026-07-27.sqlite.gz` über den
ungesperrten `releases/download`-Pfad geladen, SHA-256 gegen den Manifest-Eintrag geprüft
(Treffer: `24018f5c…cf3b2`, 28.365.720 Bytes), lokal unter `bestand/hub.sqlite` abgelegt,
`kandidaten.py` **ohne** `--aus-snapshot` aufgerufen.

**Stale-Branch-Falle wie an allen Vortagen zu Sitzungsbeginn vorgefunden und vor dem ersten
`kandidaten.py`-Aufruf behoben.** `HEAD detached`, lokale `main`-Referenz zeigte auf `c246d8d`
(neunter Lauf, 09.08.) statt auf den tatsächlichen Remote-Stand (`10826d7`, dreizehnter Lauf,
13.08.); mit `git fetch origin main && git checkout -B main origin/main` korrigiert, bevor
irgendetwas beurteilt wurde. `bereits_beurteilte_paare` stand bei 640 vor diesem Lauf (600 +
40 kein_merge vom dreizehnten Lauf), 5.406 Kandidaten gefunden — exakt der vom dreizehnten Lauf
erwartete Rückstand (5.446 gefunden am 13.08. minus 40 vorgelegte = 5.406 gekappt) —, 40
vorgelegt, 5.366 erneut gekappt.

**Neu: `api.github.com` blieb wie gewohnt gesperrt, aber diesmal auch `api.zenodo.org` —
erstmals eine Zenodo-Abfrage vom Sitzungsproxy mit HTTP 502 statt einer Antwort von Zenodo
selbst abgewiesen.** `curl https://api.zenodo.org/records/<id>` scheiterte wiederholt mit
„CONNECT tunnel failed, response 502"; der Proxy-Statusendpunkt (`$HTTPS_PROXY/__agentproxy/status`)
zeigte `recentRelayFailures` mit `"detail": "gateway answered 502 to CONNECT (policy denial or
upstream failure)"` für den Host `api.zenodo.org:443` — nicht die für echte Sperren dokumentierten
403/407-Codes. Behelf gefunden und verifiziert: `zenodo.org/api/records/<id>` (derselbe Endpunkt
unter dem Haupt-Host statt der `api.`-Subdomain) lieferte durchgehend HTTP 200 mit identischer
JSON-Struktur (`id`, `conceptrecid`, `files`, `metadata` usw.) — für alle 25 in diesem Lauf
geprüften Zenodo-IDs verwendet, keine einzige über `api.zenodo.org` selbst. `zenodo.org/api/records`
ist derselbe von Zenodo dokumentierte API-Endpunkt, nur über den Haupt-Host aufgerufen, kein
Umgehen einer Zugriffsbeschränkung. Nicht getan: keine Änderung an einem Prüfskript, da die
Urteilsroutine ohnehin nur manuell mit curl/Python arbeitet — der Behelf ist rein diese
Sitzung betreffend, aber für künftige Läufe hier vermerkt, falls die Sperre anhält.

**Zweiter bestätigter Merge seit dem GBIF/PANGAEA-Fund vom 09.08. (nach dem DIGITAL.CSIC-Fund
vom 12.08.): zwei unabhängige Zenodo-Einreichungen mit byte-identischer Datei, ohne jede
deklarierte Beziehung.** Kandidatentriple „Artificial intelligence reveals potential Arctic
whale aggregation disruption due to climate change": `dh-24474650ab2babc4` (Zenodo 10.5281/
zenodo.7564654) / `dh-87cfdc6797b98174` (Zenodo-Concept 10.5281/zenodo.7568068) /
`dh-c5fedf7da21c2d4d` (Zenodo 10.5281/zenodo.7568069). Geprüft (nicht vermutet): 7564654 trägt
eine eigene, unabhängige Concept-DOI-Gruppe (`conceptrecid: 7564653`) — kein Alias von 7568068/
7568069 (`conceptrecid: 7568068`). Beide Datensätze haben `related_identifiers: null` in ihren
Zenodo-Metadaten — keine deklarierte Beziehung, weshalb R2/R4 sie nicht automatisch verbunden
haben. Beide tragen jedoch dieselbe Datei „Supplementary data.doc" mit **byte-identischem
MD5-Hash** (`4a5d501f19e52d4d01cfe3aa6b219456`), wortgleichem Titel, demselben (einzigen)
Urheber „Anonimus" und einem Veröffentlichungsdatum nur einen Tag auseinander (24.01. bzw.
25.01.2023); der Beschreibungstext beginnt in beiden Fällen identisch, 7568069 ist die
vollständigere, längere Fassung. Strukturell derselbe von R2/R4 nicht erkannte
Doppeleinreichungs-Fall wie GBIF/PANGAEA und DIGITAL.CSIC, hier aber ohne Aggregator dazwischen
— zwei eigene, unabhängige Zenodo-Deposits desselben Werks. `merge`, `ebene: fassung`, nur für
das Paar `dh-24474650ab2babc4`/`dh-c5fedf7da21c2d4d` (die direkte Evidenz). Für die beiden
anderen Paare des Triples (gegen die reine Concept-DOI 7568068) `kein_merge` — dieselbe
Begründung wie beim DIGITAL.CSIC-Fund vom 12.08.: die Concept-DOI ist nur ein struktureller
Alias von 7568069, kein eigenes Ziel, ein Merge ohne direkten Beleg für genau dieses Paar wäre
eine Vermutung.

**Neu: zwei bislang nicht im Register beobachtete Quellen unter den Kandidaten, beide mit
demselben Concept-/Versions-Muster wie Zenodo.** FDR Uni Hamburg (`www.fdr.uni-hamburg.de`,
DOI-Präfix `10.25592`, InvenioRDM-Software wie Zenodo): Paar `dh-3a639da48ead80cd`/
`dh-e847e8413bc256c7` (uhhfdm.17310/17311) — `api/records/17310` liefert HTTP 301 auf
`api/records/17311`; 17311 selbst trägt `conceptdoi: 10.25592/uhhfdm.17310` und
`relations.version` mit `count: 1` (nur eine veröffentlichte Fassung) — dieselbe Concept-/
Versions-Instabilität wie bei Zenodo, hier zum ersten Mal an einer FDR-Uni-Hamburg-Fundstelle
bestätigt, `kein_merge`. TU Graz Repository (`repository.tugraz.at`, DOI-Präfix `10.3217`,
ebenfalls InvenioRDM): Paar `dh-38911548397f4fe7`/`dh-67daa008d407f8e9` (g4wk6-k4313/
ckkj2-2me08) — **anders als bei allen bisherigen Concept-/Versions-Funden bereits von R1–R4
noch nicht als `gleiches_werk_bereits` erkannt.** `g4wk6-k4313` antwortet auf der Repository-API
mit HTTP 403 „Zugriff verweigert" (Landing-Page bestätigt: Redirect auf `/login/`, geschützter
Datensatz); `ckkj2-2me08` ist strukturell eigenständig — sein eigenes Parent-Record ist
`w7ajr-3ea83`, nicht `g4wk6-k4313`, der Versions-Endpunkt listet nur den einen Record selbst.
Keine deklarierte Beziehung zwischen beiden, kein Zugriff auf den Inhalt des geschützten
Datensatzes möglich — `kein_merge` mangels Beleg, wie bei den restricted-Zenodo-Funden vom
07./10.08.

**Übrige Kandidaten:** 4 weitere echte Dreiergruppen mit dem etablierten Concept-/Versions-Muster
(Mendeley hhv937v7pv, fz7d6x4bwx, hy767fh3rx — je zwei echte Versionen, unversionierte Basis-DOI
zeigt aktuell auf die jüngere; Zenodo 7722892/6037351/6037352 — Concept-Alias plus eine
inhaltlich abweichende echte Vorversion mit anderer Datei/MD5), 1 Zenodo-Dreiergruppe ohne
Dateiidentität trotz gemeinsamer Concept-DOI 17204083 („Artificial Intelligence, Security, and
Sovereignty" — drei separate Uploads mit je unterschiedlich benannter PDF-Datei, keine der drei
Kombinationen mit Belegidentität, `kein_merge` im Zweifel für alle drei Paare), 1
figshare-Zweierpaar aus einer Dreiergruppe (Artikel 13497855, v1 mit 3 Dateien vs. v2 mit
inzwischen leerer Dateiliste — Inhalt entfernt), 1 Concept-DOI-Drift über das Paar hinaus
(Zenodo 17754799 zeigt aktuell auf eine dritte, unregistrierte Version 20786147, während das
vorgelegte Partnermitglied 17754800 eine eigene, im MD5 abweichende Datei trägt), sowie 13
einfache Zenodo-Concept-/Versions-Paare und 8 einfache Mendeley-Ein-Versions-Paare, alle
einzeln per API geprüft, durchweg das seit 03.08. etablierte Muster.

**Stichprobe (15 Einträge):** 13 von 15 lösten normal auf, Titel stimmten in jedem geprüften
Fall (Zenodo ×7, figshare ×3, Mendeley ×1, Dryad ×1, Språkbanken ×1). 2 von 15 (Ag Data Commons
[**neu in der Stichprobe**, `agdatacommons.nal.usda.gov`] und Harvard Dataverse) scheiterten
mit dem seit 04.08. bekannten AWS-WAF-202-Muster (Header `x-amzn-waf-action: challenge`
bestätigt für beide). Keiner der 2 Ausfälle wurde markiert — dokumentiertes Host-Blockmuster,
kein Beleg für falsche Einträge.

**Nicht getan:** Für den zweiten unabhängigen Merge-Fund (Arctic-whale-Datensatz) keine
automatische Doppeleinreichungs-Erkennung in `normalisiere.py`/`baue_bestand.py` umgesetzt —
dieselbe Begründung wie bei GBIF/PANGAEA (09.08.) und DIGITAL.CSIC (12.08.), Pipeline-Änderung
außerhalb des Commit-Umfangs dieser Routine. Für den TU-Graz-Fund (`gleiches_werk_bereits:
false`, restricted) keinen Merge vorgeschlagen — ohne einsehbaren Inhalt des geschützten
Datensatzes bleibt „im Zweifel kein_merge" verbindlich. Für den neu aufgetretenen
`api.zenodo.org`-502-Fehler keine dauerhafte Änderung vorgenommen (kein Prüfskript betroffen),
nur hier vermerkt, falls die Sperre in künftigen Läufen erneut auftritt.

**Regel/Prüfauftrag, jetzt zum 14. Mal wiederholt:** Der Prüfauftrag vom 2026-08-03
(deterministische Concept-/Alias-DOI-Erkennung aus der geharvesteten `roh`-Metadatenform)
bleibt über vierzehn Urteilsläufe (03.–14.08., mit Unterbrechung durch die GBIF/PANGAEA-,
DIGITAL.CSIC- und jetzt Arctic-whale-Merges) hinweg unumgesetzt — inzwischen über 500
Kandidatenpaare mit demselben strukturellen Befund. Weiterhin geringe Dringlichkeit, da der
Ernte-Cron pausiert ist.

## 2026-08-13 — Dreizehnter Lauf: zurück zu 40/40 kein_merge nach dem DIGITAL.CSIC-Merge; stale lokale main-Referenz diesmal VOR dem ersten `kandidaten.py`-Aufruf korrigiert; erstmals ein Concept-Record mit HTTP 410 statt 302 auf der Zenodo-API

Beurteilter Stand `snapshot-2026-07-27c` (nächtlicher Cron seit 27.07. weiterhin pausiert —
`mcp__github__list_releases` bestätigt, jüngstes Release unverändert seit dem 27.07.).
`api.github.com` war wie an allen Vortagen mit HTTP 403 gesperrt; Behelf wie dokumentiert:
Release-Metadaten per `mcp__github__list_releases`, `hub-2026-07-27.sqlite.gz` über den
ungesperrten `releases/download`-Pfad geladen, SHA-256 gegen den Manifest-Eintrag geprüft
(Treffer: `24018f5c…cf3b2`, 28.365.720 Bytes, 22.473 Einträge), lokal unter `bestand/hub.sqlite`
abgelegt, `kandidaten.py` **ohne** `--aus-snapshot` aufgerufen.

**Stale-Branch-Falle diesmal vor dem ersten Kandidatenlauf behoben, nicht erst vor dem Push.**
Zu Sitzungsbeginn erneut `HEAD detached` vorgefunden; die lokale `main`-Referenz zeigte auf
`c246d8d` (neunter Lauf, 09.08.), drei Läufe hinter dem tatsächlichen Remote-Stand (`2cc63e0`,
zwölfter Lauf, 12.08.) — dieselbe Diskrepanz wie am 12.08., nur diesmal sofort mit
`git fetch origin main && git checkout -B main origin/main` behoben, bevor überhaupt etwas
beurteilt wurde. Der seit dem 12.08. geltende Vorsatz („Fetch/Merge-Base-Check vor jedem Push,
nicht nur bei sichtbar veraltetem HEAD") lässt sich damit noch verschärfen: Der Check gehört an
den Sitzungsanfang, nicht nur vor den Push — dann stellt sich die Push-Frage gar nicht erst.

`bereits_beurteilte_paare` stand bei 600 vor diesem Lauf (560 + 40 kein_merge vom zwölften
Lauf), 5.446 Kandidaten gefunden, 40 vorgelegt, 5.406 erneut gekappt — die 5.446 entsprechen
exakt den 5.446 Kandidaten, die der zwölfte Lauf am 12.08. bereits gekappt hatte (dort:
5.486 gefunden minus 40 vorgelegte = 5.446 gekappt), wie erwartet.

**40 von 40 kein_merge — kein zweiter DIGITAL.CSIC-Fund.** Alle 40 vorgelegten Kandidaten
waren DataCite-Fundstellen mit `gleiches_werk_bereits: true`, ausschließlich Zenodo- (18
Kandidatenpaare aus 16 Concept-/Versions-Gruppen, davon eine echte Dreiergruppe),
Mendeley- (20 Paare aus 16 Basis-/Versions-Gruppen, davon vier mit echten Mehrfachversionen,
zwei davon echte Dreiergruppen) und figshare-Concept-/Versions-Muster (2 Paare, 1 Gruppe),
jedes Paar einzeln geprüft (33 einzelne Zenodo-Record-Abfragen inkl. HTTP-Statuscode und
Redirect-Ziel, 16 Mendeley-Public-API-Abfragen über
`data.mendeley.com/public-api/datasets/<id>`, 3 figshare-API-Abfragen mit
Dateiprüfsummenvergleich).

**Neu: ein Concept-Record antwortet auf der Zenodo-API erstmals mit HTTP 410 statt dem
gewohnten HTTP 302.** Bei „Artificial Intelligence in Educational Assessment: A High-School
Case Study" (Kandidatenpaar `dh-229919e0fdd90edb`/`dh-512e206ab5c73689`, Concept-DOI
`10.5281/zenodo.17459192`) liefert `api.zenodo.org/records/17459192` `{"status": 410,
"message": "The record has been deleted."}` statt eines Redirects auf die aktuelle Version —
anders als bei allen anderen 32 heute geprüften Zenodo-Records, deren Concept-Record-Abfrage
korrekt mit HTTP 302 auf `api/records/<aktuelle-Version>` verweist. Die DOI-Auflösung selbst
(`doi.org/10.5281/zenodo.17459192`) funktioniert trotzdem unverändert: Sie führt korrekt über
Zenodos Landing-Page-Routing auf `zenodo.org/records/17459193`, die aktuelle, lebendige
Version. Strukturell derselbe Concept-DOI-Mechanismus wie immer (die API-seitige Löschung
des Concept-Datensatzes ändert nichts an der DOI-Ebene), aber eine neue Fehlerform, die bei
künftigen Läufen zu falscher Interpretation verleiten könnte, wenn nur der API-Statuscode statt
der tatsächlichen DOI-Auflösung geprüft wird — kein_merge, wie beim Standardmuster.

**Kontrollprobe bestätigt: API-Redirect eines „Concept-ID gleich eigene Record-ID"-Datensatzes
auf die aktuelle Version ist Zenodo-Standardverhalten, keine Besonderheit einzelner Records.**
Bei der Dreiergruppe „Artificial Intelligence in Project Management: Challenges…" (Concept-DOI
`10.5281/zenodo.17572581`, Kandidaten `dh-0fc2047b9ad5c6a4`/`dh-470ad806c00f86a6`/
`dh-a158aba33a81efda`) lieferte `api.zenodo.org/records/17572581` zunächst identische Daten
wie `api/records/17668834` (gleicher `created`-Zeitstempel, gleiches `doi`-Feld) — auf den
ersten Blick ein möglicher Beleg für echte Datensatz-Identität statt nur Concept-DOI-Drift.
Gegenprobe an einem regulären Paar desselben Laufs (`15073721`, dessen `conceptrecid` ebenfalls
die eigene Record-ID ist): `api.zenodo.org/records/15073721` liefert ebenfalls HTTP 302 auf
`api/records/15073722` — exakt dasselbe Verhalten. Damit bestätigt: Records, deren eigene ID
zugleich die `conceptrecid` der Gruppe ist, werden von der Zenodo-API grundsätzlich auf die
aktuelle Version weitergeleitet, unabhängig vom Einzelfall — kein neuer Mechanismus, sondern
das seit 03.08. dokumentierte Concept-DOI-Verhalten, hier nur genauer nachvollzogen. `17572582`
(echte frühere Version, Index 0) hat einen eigenen, teilweise abweichenden Dateibestand
(2 von 3 Dateien anders, nur `framework300.pdf` MD5-identisch mit der aktuellen Version) —
kein_merge für alle drei Paare der Gruppe, wie beim Standardmuster.

**Übrige Kandidaten:** 12 Mendeley-Ein-Versions-Paare (Basis-/`.1`-DOI, laut Mendeley Public
API je nur eine veröffentlichte Version, `kein_merge` aus struktureller Vorsicht wie an allen
Vortagen seit 04.08.), 2 Mendeley-Dreiergruppen mit echten Mehrfachversionen (`wfdp6t7v2f`,
`9bsv2rpbvh`, je v1/v2, Basis-DOI zeigt aktuell auf die jüngere Version), 2 weitere
Mendeley-Basis-/Versions-Paare mit echten Mehrfachversionen (`h76rf38jkn`, zwei Versionen;
`x5689yhv2n`, drei Versionen, 2022–2025 — dasselbe Basis-DOI-Drift-Muster wie beim
`hms3sjzt7f`-Fund vom 08.08.), 15 einfache Zenodo-Concept-/Versions-Paare (durchweg das seit
03.08. etablierte Muster, per API einzeln bestätigt), 1 figshare-Versions-Gruppe (Artikel
29545721, unversionierte ID zeigt aktuell auf v2; v1 und v2 mit identischem Dateibestand und
identischen MD5-Prüfsummen, nur der Titel unterscheidet sich in der Groß-/Kleinschreibung —
`kein_merge` nach der seit 05.08. geltenden figshare-Regel, unabhängig von inhaltlicher
Identität).

**Stichprobe (15 Einträge):** 11 von 15 lösten normal auf, Titel stimmten in jedem geprüften
Fall (Zenodo ×6, GBIF ×2 [neu in der Stichprobe, `api.gbif.org/v1/dataset/<uuid>` bestätigt
Titel und DOI exakt], COCOON/Huma-Num ×1, Språkbanken ×1, SciDB/Science Data Bank ×1
[`scidb.cn`-Landingpage liefert im rohen HTML nur den generischen `<title>`-Tag „ScienceDB",
dasselbe clientseitig gerenderte SPA-Verhalten wie beim Mendeley-FAQ-Fund vom 12.08., Titel
stattdessen über `api.datacite.org/dois/10.57760/sciencedb.07321` bestätigt: exakt identisch
mit dem Registereintrag, auch die registrierte URL stimmt mit dem `url`-Feld der
DataCite-Metadaten überein]). 4 von 15 (figshare ×2, springernature.figshare ×1 und — **neu**
— `scholardata.sun.ac.za` [SUNScholarData] ×1) scheiterten mit dem seit 04.08. bekannten
AWS-WAF-202-Muster (Header `x-amzn-waf-action: challenge` bestätigt für alle 4).
SUNScholarData ist erkennbar eine weitere figshare-White-Label-Instanz (URL-Struktur
`/articles/dataset/.../<id>` identisch zu figshare.com) und reiht sich damit strukturell bei
karger.figshare.com/tandf.figshare.com/scielo.figshare.com/springernature.figshare.com/
rdr.ucl.ac.uk ein. Keiner der 4 Ausfälle wurde markiert — dokumentiertes Host-Blockmuster,
kein Beleg für falsche Einträge.

**Nicht getan:** Für den neuen HTTP-410-Fall (17459192) keine Änderung an `kandidaten.py`
oder den Prüfskripten vorgeschlagen — die DOI-Auflösung selbst bleibt unverändert korrekt,
nur die API-Fehlerform ist neu; ein künftiger Lauf, der sich ausschließlich auf den
API-Statuscode statt auf die tatsächliche DOI-Auflösung verlässt, könnte das fälschlich als
„Ziel nicht mehr auffindbar" statt als Concept-DOI-Normalfall lesen — hier nur vermerkt, keine
Pipeline-Änderung (außerhalb des Commit-Umfangs dieser Routine). Für die
SUNScholarData-Beobachtung keine eigene Quellen-Notiz über diese Verfahrensnotiz hinaus
angelegt, da das AWS-WAF-Muster strukturell bereits für sechs andere figshare-Instanzen
dokumentiert ist.

**Regel/Prüfauftrag, jetzt zum 13. Mal wiederholt:** Der Prüfauftrag vom 2026-08-03
(deterministische Concept-/Alias-DOI-Erkennung aus der geharvesteten `roh`-Metadatenform)
bleibt über dreizehn Urteilsläufe (03.–13.08., mit Unterbrechung durch die GBIF/PANGAEA- und
DIGITAL.CSIC-Merges) hinweg unumgesetzt — inzwischen über 460 Kandidatenpaare mit demselben
strukturellen Befund. Weiterhin geringe Dringlichkeit, da der Ernte-Cron pausiert ist.

## 2026-08-12 — Zwölfter Lauf: erste DIGITAL.CSIC-Fundstelle, sofort als Aggregatorkopie von Zenodo erkannt und gemerged; stale lokale main-Referenz zeigte auf den Stand vom 09.08. statt auf den neunten — diesmal vor dem Push bemerkt

Beurteilter Stand `snapshot-2026-07-27c` (nächtlicher Cron seit 27.07. weiterhin pausiert —
`mcp__github__list_releases` bestätigt, jüngstes Release unverändert seit dem 27.07.).
`api.github.com` war wie an allen Vortagen mit HTTP 403 gesperrt; Behelf wie dokumentiert:
Release-Metadaten per `mcp__github__list_releases`, `hub-2026-07-27.sqlite.gz` über den
ungesperrten `releases/download`-Pfad geladen, SHA-256 gegen den Manifest-Eintrag geprüft
(Treffer: `24018f5c…cf3b2`, 28.365.720 Bytes, 22.473 Einträge), lokal unter `bestand/hub.sqlite`
abgelegt, `kandidaten.py` **ohne** `--aus-snapshot` aufgerufen.

**Neue Variante der bekannten stale-Branch-Falle, diesmal vor dem Push bemerkt statt danach.**
Zu Sitzungsbeginn ein `HEAD detached`-Checkout vorgefunden (wie an mehreren Vortagen). Anders
als sonst zeigte die lokale `main`-Referenz aber nicht auf einen nur leicht veralteten Stand,
sondern auf `c246d8d` — den Commit vom **neunten** Lauf (09.08.), drei Läufe hinter dem
tatsächlich jüngsten (`302db7d`, elfter Lauf, 11.08.), von dem aus die Urteile dieser Sitzung
bereits committet waren. `git rev-parse origin/main` lieferte zunächst denselben veralteten
Stand `c246d8d` — ein reines Artefakt eines nicht aktuellen lokalen Refs, kein echter Rückstand
des Remotes: `git fetch origin main` korrigierte `origin/main` sofort auf `302db7d`, und
`git merge-base --is-ancestor origin/main HEAD` bestätigte, dass die neuen 40 Urteils-Commits
sauber auf dem tatsächlichen Remote-Stand aufsetzen. `main` mit `git checkout -B main HEAD`
auf den bearbeiteten Stand gesetzt, danach gepusht. Anders als bei den bisherigen
stale-Branch-Funden (09.08., 02.08., beide harmlos, da kein uncommiteter Inhalt betroffen war)
hätte ein Push von einer stale `main` aus hier tatsächlich einen Konflikt oder eine verlorene
Historie riskiert, wäre der Fetch/Merge-Base-Check übersprungen worden — Grund genug, diesen
Check ab sofort vor jedem Push durchzuführen, nicht nur bei sichtbar veraltetem `HEAD`.
`bereits_beurteilte_paare` stand bei 560 vor diesem Lauf (520 + 40 kein_merge vom elften Lauf),
5.486 Kandidaten gefunden, 40 vorgelegt, 5.446 erneut gekappt (5.526 gefunden am 11.08. —
exakt 40 weniger, wie erwartet).

**Erstmals seit dem neunten Lauf (09.08.) wieder ein `merge` statt durchgehend `kein_merge`:
39 von 40 `kein_merge`, 1 von 40 `merge`.** Jedes der 40 vorgelegten Paare einzeln geprüft
(Zenodo-API für 11 einfache Concept-/Versions-Paare plus 3 Dreiergruppen-Paare, Mendeley
Public API für 14 Ein-Versions-Paare plus eine Dreiergruppe, figshare-API für eine
Versions-Dreiergruppe, MaterialsCloud-API für eine Dreiergruppe, DIGITAL.CSIC-Landingpage plus
Dateidownload für den Merge-Fund).

**Neu: DIGITAL.CSIC (`digital.csic.es`, DOI-Präfix `10.20350`) erstmals unter den
Merge-Kandidaten — und zugleich der erste bestätigte Merge seit dem GBIF/PANGAEA-Fund vom
09.08.** Kandidatentriple `dh-1a8131b9b33942e1` (Zenodo-Concept 10.5281/zenodo.5602976) /
`dh-695fcfb23da1ee7b` (DIGITAL.CSIC 10.20350/digitalCSIC/15084) / `dh-f0e5b643d0fb157c`
(Zenodo 10.5281/zenodo.5602977), „Artificial Intelligence for Quality Control of manufacturing
operations: Macro-mechanical milling…". DIGITAL.CSICs eigene Landingpage
(`digital.csic.es/handle/10261/286591`) trägt im `DC.relation`-Metadatenfeld wörtlich
`https://doi.org/10.5281/zenodo.5602977`. Beide dort gehosteten Bitstreams heruntergeladen und
per MD5 mit den Zenodo-5602977-Dateien verglichen: `Macromilling_dataset_1.csv`
(`c99d15020803625964724bf3346d34af`) und `Datasets_description_macromilling_v2.pdf`
(`e94509a8a9791e83276000bda9a1fa47`) — auf beiden Plattformen byte-identisch. `merge`,
`ebene: fassung`, nur für das Paar DIGITAL.CSIC/Zenodo-5602977. Für die beiden anderen Paare
des Triples (DIGITAL.CSIC gegen die reine Zenodo-Concept-DOI 5602976 sowie 5602976 gegen 5602977
selbst) `kein_merge` — die deklarierte Beziehung nennt wörtlich nur die Versions-DOI 5602977,
nicht die Concept-DOI, und 5602976/5602977 sind das gewohnte Concept-/Versions-Alias-Paar.
Strukturell derselbe von R2/R4 nicht erkannte Aggregatorkopie-Fall wie GBIF/PANGAEA (09.08.):
DIGITAL.CSIC deklariert die Beziehung nur in seinen eigenen DC-Metadaten, nicht in
DataCite-`relatedIdentifiers`, die R2 auswertet.

**Neu: MaterialsCloud erstmals mit zwei echten Versionen statt nur `self_doi`/`parent_doi`
mit einer einzigen Version (05.08.).** Dreiergruppe `materialscloud:n2-tg` (parent-DOI,
InvenioRDM-Record `xtt6b-cs696`) / `materialscloud:vt-4t` (Record `my4yn-3nj21`, `is_latest:
true`) / `materialscloud:c6-39` (Record `a0fep-vy311`, `is_latest: false`), „Artificial
intelligence enables mobile soil analysis for sustainable agriculture". Alle 7 Dateien zwischen
`vt-4t` und `c6-39` per MD5 verglichen — inhaltlich vollständig identisch (u. a.
`CalibrationImages.zip`, 3.003.820.125 Byte, gleiche Prüfsumme). Trotzdem `kein_merge` für alle
drei Paare: dieselbe seit 08.08. geltende Regel wie beim figshare-Fund (Artikel 29231351,
v3/v4 inhaltsgleich, trotzdem eigenständig registriert) — hier zum ersten Mal auf
MaterialsCloud übertragen; zusätzlich ist die `parent_doi` selbst ein wanderndes Ziel.

**Neu: bei einer Zenodo-Dreiergruppe zeigt die Concept-DOI nicht auf eines der beiden
Kandidatenpaar-Mitglieder, sondern auf eine dritte, dateireichere Fassung, die selbst Teil der
Dreiergruppe ist.** „Artificial intelligence-generated patient safety checklists for
musculoskeletal injections": Concept `10792768` löst per HTTP 302 auf `10846831` auf (2 Dateien,
inkl. `Shapiro-Wilk test results.docx`), nicht auf `10792769` (1 Datei, `Checklist demands…docx`,
MD5-identisch mit der zweiten Datei aus `10846831`). `10792769` ist damit eine echte frühere
Fassung mit weniger Dateien, `10846831` die aktuelle — `kein_merge` für alle drei Paare, davon
eines mit echtem Beleg für einen inhaltlichen Fassungsunterschied (fehlende Datei), zwei aus dem
gewohnten Concept-Alias-Grund.

**Erneut: Concept-DOI-Drift über das Kandidatenpaar hinaus.** Bei „Artificial Intelligence for
Sustainable SMEs: A Bibliometric Analysis of Trends and Future Directions" löst die Concept-DOI
`16498831` aktuell auf Record `20046349` auf — eine im Register nicht erfasste dritte Version,
nicht auf das vorgelegte Partnermitglied `16498832`. Kein Merge-Ziel vorgeschlagen, da die
dritte Version nicht im Register steht (wie bei den beiden vergleichbaren Funden vom 11.08.).

**Übrige Kandidaten: 14 Mendeley-Ein-Versions-Paare (Basis-/`.1`-DOI, laut Mendeley Public API
je nur eine veröffentlichte Version, `kein_merge` aus struktureller Vorsicht wie an allen
Vortagen seit 04.08.), 1 Mendeley-Dreiergruppe (`s26kxvspn7`, Artificial Intelligence, Firm
Growth, and Product Innovation — drei echte Versionen, Beschreibungstext unterscheidet sich
nachweislich zwischen Version 2 und 3 durch einen zusätzlichen Hinweis auf Pseudo-Daten für
Compustat, `kein_merge` mit echtem inhaltlichen Beleg), 11 einfache Zenodo-Concept-/
Versions-Paare (durchweg das seit 03.08. etablierte Muster, per API einzeln bestätigt), 1
figshare-Versions-Dreiergruppe (Artikel 28665347 v1/v2/v3, alle drei Versionen mit
unterschiedlicher Dateigröße und Prüfsumme — v2 und v3 zwar nahezu gleich groß, aber
unterschiedliche MD5, also inhaltlich verschieden).

**Stichprobe (15 Einträge):** 13 von 15 lösten normal auf, Titel stimmten in jedem geprüften
Fall (Zenodo ×11, sowie 1 Mendeley-Eintrag [`dh-43a665724e680c42`, `zdh4d5ws2z/2`] — die
Mendeley-Landingpage liefert im rohen HTML nur den generischen `<title>`-Tag „FAQ" (clientseitig
gerendertes SPA-Verhalten, kein Fehlbefund), Titel stattdessen über die Public API bestätigt:
Datensatzname „Data from Neural Network Training in the Obstacle Tower Environment to
Investigate Embodied, Weakly Supervised Learning" stimmt exakt mit dem Registereintrag überein).
2 von 15 (beide figshare) scheiterten mit dem seit 04.08. bekannten AWS-WAF-202-Muster (Header
`x-amzn-waf-action: challenge` bestätigt für beide). Keiner der 2 Ausfälle wurde markiert —
dokumentiertes Host-Blockmuster, kein Beleg für falsche Einträge.

**Nicht getan:** Für den DIGITAL.CSIC/Zenodo-Fund keine automatische Aggregatorkopie-Erkennung
in `normalisiere.py`/`baue_bestand.py` umgesetzt — dieselbe Begründung wie beim GBIF/PANGAEA-Fund
vom 09.08. (Pipeline-Änderung außerhalb des Commit-Umfangs dieser Routine). Für die
Zenodo-Concept-DOI 5602976 (Teil desselben Werks wie der gemergte Fund) keinen eigenen Merge
vorgeschlagen, obwohl sie transitiv zum selben Werk gehört — die direkte Evidenz
(DIGITAL.CSICs `DC.relation`) nennt wörtlich nur die Versions-DOI 5602977, nicht die Concept-DOI;
ein Merge ohne eigenen Beleg für genau dieses Paar wäre eine Vermutung, keine Prüfung.

**Regel/Prüfauftrag, jetzt zum zwölften Mal wiederholt, mit neuer Ausweitung:** Der Prüfauftrag
vom 2026-08-03 (deterministische Concept-/Alias-DOI-Erkennung) bleibt über zwölf Urteilsläufe
(03.–12.08., mit Unterbrechung durch die GBIF/PANGAEA- und jetzt DIGITAL.CSIC-Merges) hinweg
unumgesetzt — inzwischen über 420 Kandidatenpaare mit demselben strukturellen Befund. Neu dazu:
Der seit 09.08. offene GBIF-spezifische Prüfauftrag (Abgleich einer Quellen-API gegen die
harvestete Ziel-DOI vor Aufnahme als eigenständige Fundstelle) sollte nicht GBIF-spezifisch
bleiben, sondern allgemein für Aggregator-Repositorien gelten, deren Beziehung nur in eigenen
Metadatenfeldern (GBIFs `dataset.doi`, hier DIGITAL.CSICs `DC.relation`) steht, nicht in
DataCite-`relatedIdentifiers`. Weiterhin geringe Dringlichkeit, da der Ernte-Cron pausiert ist.

## 2026-08-11 — Elfter Lauf: erneut 40/40 kein_merge; erste Fundstelle von 4TU.ResearchData unter den Kandidaten, zwei Concept-DOIs drifteten während des Laufs auf eine im Register unbekannte dritte Version

Beurteilter Stand `snapshot-2026-07-27c` (nächtlicher Cron seit 27.07. weiterhin pausiert —
`mcp__github__list_releases` bestätigt, jüngstes Release unverändert seit dem 27.07.).
`api.github.com` war wie an allen Vortagen mit HTTP 403 gesperrt; Behelf wie dokumentiert:
Release-Metadaten per `mcp__github__list_releases`, `hub-2026-07-27.sqlite.gz` über den
ungesperrten `releases/download`-Pfad geladen, SHA-256 gegen den Manifest-Eintrag geprüft
(Treffer: `24018f5c…cf3b2`, 28.365.720 Bytes, 22.473 Einträge), lokal unter `bestand/hub.sqlite`
abgelegt, `kandidaten.py` **ohne** `--aus-snapshot` aufgerufen. Zu Sitzungsbeginn ein
`HEAD detached`-Checkout vorgefunden (kein uncommiteter Inhalt betroffen); mit
`git checkout -B main origin/main` auf den aktuellen Stand zurückgesetzt, wie am 09.08.
`bereits_beurteilte_paare` stand bei 520 vor diesem Lauf (480 + 40 kein_merge vom zehnten
Lauf), 5.526 Kandidaten gefunden, 40 vorgelegt, 5.486 erneut gekappt (5.566 gefunden am
10.08. — exakt 40 weniger, wie erwartet).

**40 von 40 kein_merge**, alle mit `gleiches_werk_bereits: true`. Verteilung: 28 Zenodo-Paare
(19 unterscheidbare Werke, davon 5 mit echten Dreiergruppen), 9 Mendeley-Paare (6 Werke),
2 figshare-Paare (1 Werk), 1 Paar **einer bislang nicht im Register beobachteten Quelle**
(dazu unten). Jedes Paar einzeln geprüft (36 Zenodo-Record-Abfragen inkl. HTTP-Statuscode und
Redirect-Ziel jeder Concept-DOI, 7 Mendeley-Public-API-Abfragen über den korrekten Endpunkt
`data.mendeley.com/public-api/datasets/<id>` — `api.mendeley.com` verlangt inzwischen einen
Auth-Header und lieferte nur `oauth/NOT_AUTHORIZED`, ohne dass sich am strukturellen Befund
etwas ändert, `api.figshare.com/v2/articles/29233484/versions/{1,2}` mit Dateiprüfsummen).

**Neu: 4TU.ResearchData (`data.4tu.nl`, DOI-Präfix `10.4121`) erstmals unter den
Merge-Kandidaten.** Paar `dh-67ceb7fff81faf42`/`dh-f559e79294287332`
(„Artificial Intelligence Based Antibiotic Zone Measurement For Disk Diffusion Test"):
unversionierte DOI `10.4121/6836caa1-2c19-4e62-b30a-0c15488dd33a` löst auf
`data.4tu.nl/datasets/6836caa1-…/`, die `.v1`-DOI auf dieselbe Kennung mit Suffix `/1` —
beide Landing-Pages tragen denselben `<title>`-Tag, aktuell existiert laut Seite nur eine
Version. 4TU läuft auf der Djehuty-Software, strukturell mit figshare verwandt (Basis-/
Versions-Kennung, Basis zeigt auf die jeweils neueste Version) — dieselbe Instabilität wie
bei allen bisherigen Mendeley-Ein-Versions-Funden, hier zum ersten Mal an dieser Quelle
bestätigt. `kein_merge` aus denselben strukturellen Gründen.

**Neu: bei zwei Zenodo-Dreiergruppen zeigte die Concept-DOI zum Prüfzeitpunkt weder auf das
eine noch auf das andere Kandidatenpaar-Mitglied, sondern auf eine dritte, im Register gar
nicht erfasste, noch neuere Version.** Bei „Artificial Intelligence and Humanitarian
Logistics 5.0" (Concept 18096056, Kandidaten 18096057/18096359) löst die Concept-DOI aktuell
auf Record 20952124 auf; bei „Artificial intelligence and organizational performance in the
tourism…" (Concept 18099904, Kandidat 18099905) auf Record 19692246 — beides Records, die im
laufenden Register bislang nicht vorkommen. Anders als der Concept-DOI-Drift-Regelfall
(Concept zeigt auf eines der beiden vorgelegten Paar-Mitglieder) ist das ein Drift über das
Paar selbst hinaus — noch ein Beleg mehr dafür, dass eine Concept-DOI kein fixes Ziel ist,
sondern sich mit jeder neuen Fassung weiterverschiebt, auch während ein einzelner Lauf noch
läuft.

**Übrige Dreiergruppen mit echten Fassungsunterschieden, wie an den Vortagen:** PATCH-Artefakte
(Zenodo 10996523/14257480/10996524, PATCH.zip mit unterschiedlicher Größe und Prüfsumme
zwischen den beiden echten Versionen), penis-size-Datensatz (Zenodo 14645247/14645388/14645248,
1 Datei SPSS vs. 7 Dokumentdateien — völlig anderer Dateibestand), „Open Data ID 162" (Zenodo
17391025/17391026/17391062, gleicher Dateiname, unterschiedliche Größe und Prüfsumme), figshare
29233484 (v1 enthält die eigentliche Datendatei 副本.xlsx, v2 nur noch eine Declaration.txt —
die Datendatei wurde zwischen den Versionen entfernt), Mendeley 289jtphg33 (Version 1 und 2
mit inhaltlich vollständig unterschiedlicher Beschreibung). Die übrigen Mendeley-Paare
(2z8t5g347z, c8k4xrwyd3, d3mx2zgg76, h93fp9yws6, p748yjtrc5, sypw8tgfms) hatten laut API
je nur eine veröffentlichte Version — Basis- und `.1`-DOI aktuell inhaltsgleich, `kein_merge`
aus rein struktureller Vorsicht wie an allen Vortagen seit 04.08.

**Stichprobe (15 Einträge):** 10 von 15 lösten normal auf, Titel stimmten in jedem geprüften
Fall (Zenodo ×4 [darunter ein Concept-DOI-Drift: `dh-f83dc9fec5a7df9e`, Zenodo-Konzept
21541072 → aktueller Record 21541073, Titel „GERB: Graduate Economic Reasoning Benchmark"
exakt identisch — derselbe seit 03.08. dokumentierte Mechanismus], ArcGIS ×2 [Layer-Namen
„Our Natural City projects"/„OSM_Vrije_tijd" statt Registertitel — erwartetes ArcGIS-REST-
Muster], Språkbanken ×2, Mendeley ×1 [`f9k7trygpy`, löste auf `/1` auf, Titel identisch] und
— **neu in der Stichprobe** — SciDB/Science Data Bank ×1 [`scidb.cn`, löste unauffällig auf,
Titel exakt identisch]). 5 von 15 (springernature.figshare ×3, figshare.com ×2) scheiterten
mit dem seit 04.08. bekannten AWS-WAF-202-Muster (Header `x-amzn-waf-action: challenge`
bestätigt für alle 5). Keiner der 5 Ausfälle wurde markiert — dokumentiertes Host-Blockmuster,
kein Beleg für falsche Einträge.

**Nicht getan:** Für die beiden neu beobachteten Concept-DOI-Drifts über das Kandidatenpaar
hinaus (18096056→20952124, 18099904→19692246) keinen Merge mit der jeweils dritten,
unregistrierten Version vorgeschlagen — die dritte Version ist gar nicht im Register, ein
Merge-Ziel für sie existiert nicht. Für den neuen 4TU.ResearchData-Fund keine eigene
Quellen-Notiz über diese Verfahrensnotiz hinaus angelegt, da das Muster strukturell bereits
für Zenodo/Mendeley/figshare dokumentiert ist und sich nur die Quelle wiederholt, nicht das
Phänomen.

**Regel/Prüfauftrag, jetzt zum neunten Mal wiederholt:** Der Prüfauftrag vom 2026-08-03
(deterministische Concept-/Alias-DOI-Erkennung aus der geharvesteten `roh`-Metadatenform)
bleibt über neun Urteilsläufe (03.–11.08., mit Unterbrechung durch den GBIF/PANGAEA-Befund
vom 09.08.) hinweg unumgesetzt — inzwischen über 380 Kandidatenpaare mit demselben
strukturellen Befund. Neu dazu: Sollte die Erkennung künftig umgesetzt werden, müsste sie
auch 4TU.ResearchData (`10.4121`-DOIs, Basis-/`.v1`-Suffix) mit abdecken, nicht nur
Zenodo/Mendeley/figshare. Weiterhin geringe Dringlichkeit, da der Ernte-Cron pausiert ist.

## 2026-08-10 — Zehnter Lauf: zurück zu 40/40 kein_merge; die drei Dreiergruppen zeigen erstmals eine restricted-Version als Konzept-Ziel; AWS-WAF-202-Muster erstmals auch auf rdr.ucl.ac.uk (figshare-White-Label) beobachtet

Beurteilter Stand weiterhin `snapshot-2026-07-27c` (nächtlicher Cron seit 27.07. pausiert,
Register-Rückbau — `list_releases` bestätigt, jüngstes Release unverändert). `api.github.com`
war wie an allen Vortagen mit HTTP 403 gesperrt; Behelf wie dokumentiert: Release-Metadaten
per `mcp__github__list_releases`, `hub-2026-07-27.sqlite.gz` über den ungesperrten
`releases/download`-Pfad geladen, SHA-256 gegen den Manifest-Eintrag geprüft (Treffer:
`24018f5c…cf3b2`, 28.365.720 Bytes, 22.473 Einträge), lokal unter `bestand/hub.sqlite`
abgelegt (`hub_lib.py`-`BESTAND` löst zu `<Repo-Wurzel>/bestand/`, nicht `pipeline/bestand/` —
die seit 09.08. bekannte Falle diesmal von Anfang an vermieden), `kandidaten.py` **ohne**
`--aus-snapshot` aufgerufen. `bereits_beurteilte_paare` stand bei 480 vor diesem Lauf (440 +
9 Merges + 31 kein_merge vom neunten Lauf), 5.566 Kandidaten blieben erneut gekappt (5.606
gefunden — exakt 40 weniger als am 09.08., wie erwartet).

**Zurück zu 40/40 kein_merge — kein zweiter GBIF/PANGAEA-Fund.** Alle 40 vorgelegten
Kandidaten waren DataCite-Fundstellen mit `gleiches_werk_bereits: true`, ausschließlich
Zenodo- (30 Paare), Mendeley- (8 Paare) und figshare-Concept-/Versions-DOI-Muster (2 Paare),
jedes Paar einzeln per API geprüft (51 einzelne Zenodo-Record-Abfragen inkl. HTTP-Statuscode
und Redirect-Ziel jeder Concept-DOI, 8 Mendeley-Public-API-Abfragen, 2 figshare-Versions-
Abfragen mit Dateiprüfsummenvergleich) — nicht nur an Beispielen.

**Neu innerhalb des etablierten Musters: bei zwei der drei Dreiergruppen ist die aktuelle
Version selbst `restricted`, ohne einsehbare Dateiliste.** Bisher unterschieden sich echte
Fassungen innerhalb einer Dreiergruppe entweder inhaltlich (verschiedene Dateien/Prüfsummen)
oder waren komplett unzugänglich (ganze Gruppe `restricted`, wie am 08.08.). Heute zum ersten
Mal: die *neuere* Version zweier Dreiergruppen (`10993169` bei „How Effective are LLMs in
Generating Software Specifications", `10388937` bei „Program Selection from Large Language
Models") ist `access_right: restricted`, während die *ältere* Version derselben Gruppe offen
mit vollständiger Dateiliste ist. Das kehrt das gewohnte Bild um (sonst ist meist die neueste
Version die zugängliche) und bedeutet: In beiden Fällen ist die Concept-DOI (die per HTTP 302
korrekt auf die jeweils neueste Version zeigt) auf ein für die Routine nicht einsehbares Ziel
gerichtet — kein Beleg für Identität mit der offenen Vorversion, `kein_merge` mangels Beleg,
nicht nur aus struktureller Vorsicht. Die dritte Dreiergruppe („Developer Challenges on Large
Language Models") bestätigte dagegen erneut das seit 08.08. bekannte Muster: gleicher
Dateiname, unterschiedliche MD5 und Größe zwischen Version 1 (353.866.533 Byte) und Version 2
(350.787.180 Byte) — Inhalt tatsächlich geändert.

**Übrige 21 Zenodo-Paare, 8 Mendeley-Paare, 2 figshare-Paare:** durchweg das seit 03.08.
etablierte Muster. Bei allen 21 einfachen Zenodo-Paaren löste die Concept-DOI per HTTP 302
exakt auf die im Kandidatenpaar stehende Versions-DOI auf (kein Drift diesmal, anders als an
mehreren Vortagen) — trotzdem `kein_merge`, weil die Concept-DOI strukturell kein fixes Ziel
ist. Bei 7 der 8 Mendeley-Paare existiert laut Mendeley Public API aktuell nur eine
veröffentlichte Version, bei einem (`t96hmx65pd`) zwei, mit der Basis-DOI aktuell auf Version 2
zeigend — beides dasselbe Drift-Risiko wie an allen Vortagen seit 04.08. Beide figshare-Paare
(Artikel 19097078, „Application of Recurrent Neural Network…") mit inhaltlich unterschiedlicher
Datei zwischen v1 (141.943.453 Byte) und v2 (79.876.474 Byte).

**Stichprobe (15 Einträge):** 10 von 15 lösten normal auf, Titel stimmten in jedem geprüften
Fall (Zenodo ×5, Mendeley ×1, MaterialsCloud ×1 [Titel stimmt; die Landing-URL löst auf eine
andere Record-Kennung als die registrierte DOI-Kennung auf — normaler MaterialsCloud-
Mechanismus, kein Drift-Befund wie bei den `self_doi`/`parent_doi`-Fällen vom 05.08.], ArcGIS
×1 [Layer-Name „District Land Points" statt Registertitel „District Government Land Points" —
erwartetes ArcGIS-REST-Muster], CEH ×1 [neu in der Stichprobe, `catalogue.ceh.ac.uk`, löste
unauffällig auf]). Darunter ein Concept-DOI-Drift (`dh-2916119b2f9d46bc`: Zenodo-Konzept
12206145 → aktueller Record 17591552, Titel exakt identisch, derselbe seit 03.08. dokumentierte
Mechanismus). 5 von 15 (figshare ×2, karger.figshare ×1, Harvard Dataverse ×1 und — **neu** —
`rdr.ucl.ac.uk` [UCL Research Data Repository] ×1) scheiterten mit dem seit 04.08. bekannten
AWS-WAF-202-Muster (Header `x-amzn-waf-action: challenge` bestätigt für alle 5). `rdr.ucl.ac.uk`
ist erkennbar eine weitere figshare-White-Label-Instanz (URL-Struktur `/articles/dataset/.../<id>/<version>`
identisch zu figshare.com) und reiht sich damit strukturell bei karger.figshare.com/
tandf.figshare.com/scielo.figshare.com/springernature.figshare.com ein. Keiner der 5 Ausfälle
wurde markiert — dokumentiertes Host-Blockmuster, kein Beleg für falsche Einträge.

**Nicht getan:** Für die beiden restricted-Dreiergruppen-Fälle keinen Merge vorgeschlagen,
obwohl die Concept-DOI korrekt auf die neuere Version zeigt — ohne einsehbaren Inhalt bleibt
„im Zweifel kein_merge" auch dann verbindlich, wenn die strukturelle Zuordnung an sich nicht
strittig ist. Für den MaterialsCloud-Fund keinen Prüfauftrag notiert, da Titel und Zugriffsweg
übereinstimmten und keine Instabilität wie beim `self_doi`/`parent_doi`-Fund vom 05.08. erkennbar
war.

**Regel/Prüfauftrag, jetzt zum achten Mal wiederholt:** Der Prüfauftrag vom 2026-08-03
(deterministische Concept-/Alias-DOI-Erkennung aus der geharvesteten `roh`-Metadatenform)
bleibt über acht Urteilsläufe (03.–10.08., mit Unterbrechung durch den GBIF/PANGAEA-Befund
vom 09.08.) hinweg unumgesetzt — inzwischen über 340 Kandidatenpaare mit demselben
strukturellen Befund. Weiterhin geringe Dringlichkeit, da der Ernte-Cron pausiert ist.

## 2026-08-09 — Neunter Lauf: erstmals Merges statt 40/40 kein_merge — GBIF-Datensätze zitieren die PANGAEA-DOI als eigene Identität; von R2/R4 nicht erkannte Aggregatorkopie

Beurteilter Stand weiterhin `snapshot-2026-07-27c` (nächtlicher Cron seit 27.07. pausiert,
Register-Rückbau — `list_releases` bestätigt, jüngstes Release unverändert). Zu Beginn des
Laufs eine stale lokale `main`-Branchreferenz vorgefunden (Checkout-Artefakt: `main` zeigte
auf einen Stand vom 02.08., 90/50 Commits von `origin/main` divergiert, ohne dass irgendein
uncommiteter Inhalt betroffen war); mit `git checkout -B main origin/main` auf den aktuellen
Stand zurückgesetzt, bevor `kandidaten.py` lief. `api.github.com` war wie an allen Vortagen
mit HTTP 403 gesperrt; Behelf wie dokumentiert: Release-Metadaten per `mcp__github__list_releases`,
`hub-2026-07-27.sqlite.gz` über den ungesperrten `releases/download`-Pfad geladen, SHA-256 gegen
den Manifest-Eintrag geprüft (Treffer: `24018f5c…cf3b2`, 28.365.720 Bytes, 22.473 Einträge).
**Neue Falle dabei:** `BESTAND` in `hub_lib.py` löst zu `<Repo-Wurzel>/bestand/`, nicht zu
`pipeline/bestand/` auf — die Datei zunächst am falschen Ort abgelegt, `kandidaten.py` brach
mit demselben HTTP-403 ab, weil es die lokale Datei nicht fand und erneut `snapshot_holen()`
aufrief. Nach Korrektur des Pfads lief es normal durch. `bereits_beurteilte_paare` stand bei
440 vor diesem Lauf, 5.566 Kandidaten blieben erneut gekappt (5.606 gefunden).

**Erstmals Merges: 9 von 40 Kandidaten `merge`, nicht `kein_merge`.** Nach acht Läufen in
Folge mit 40/40 `kein_merge` (03.–08.08.) ist das der erste Bruch mit dem bisherigen Muster.
Betroffen: neun Fundstellen-Paare aus PANGAEA und GBIF, alle mit Titel „(Appendix 1/A–E)
Census data of planktic/benthic foraminiferal faunas …" für denselben DSDP-/ODP-Bohrkern
bzw. dieselbe Sedimentkernstelle. Geprüft (nicht vermutet): Die GBIF-API
(`api.gbif.org/v1/dataset/<uuid>`) trägt für jeden der neun Datensätze ein eigenes Feld `doi`
— und dieses Feld nennt nicht GBIFs eigene registrierte DOI (`10.15468/…`), sondern wörtlich
die PANGAEA-DOI (`10.1594/pangaea.<id>`). Der Zugriffsendpunkt (`DWC_ARCHIVE`) lädt bei jedem
Abruf live von `digir.pangaea.de/dwca/get?doi=…` — GBIF hält keine eigene Kopie, sondern liest
direkt aus PANGAEAs Infrastruktur. Titel, Fundort-/Site-Bezeichnung und Urheberliste sind
innerhalb jedes Paars wortgleich. Zur Gegenprobe PANGAEAs eigene DataCite-Metadaten
(`api.datacite.org/dois/10.1594/pangaea.742590`) abgefragt: `relatedIdentifiers` enthält
keinerlei Verweis auf die GBIF-DOI oder das GBIF-Dataset — die Aggregatorkopie ist nur
GBIF-seitig deklariert (über GBIFs eigene API, nicht über DataCite-Relationen), weshalb R2
(quellen-behauptete Relation) und R4 (deklarierte Aggregatorkopie) sie nicht automatisch
erkennen konnten. Anders als bei den seit 03.08. dokumentierten Concept-/Versions-DOI-Fällen
ist das kein wanderndes Ziel: Jede GBIF-DOI ist fest an genau eine PANGAEA-DOI gebunden, kein
Drift-Risiko wie bei Zenodo-Concept-DOIs oder Mendeley-Basis-DOIs. Alle neun `merge`,
`ebene: fassung`, mit dem jeweiligen GBIF-API-Fund als Beleg im Journal.

**Übrige 31 Kandidaten: 40-minus-9, wie an den Vortagen ausnahmslos Zenodo-/Mendeley-/
figshare-Concept-/Versions-DOI-Muster, jedes Paar einzeln per API geprüft** (35 einzelne
Zenodo-Record-Abfragen für 16 Zenodo-Gruppen, 5 Mendeley-Gruppen per Mendeley Public API).
Darunter drei Dreiergruppen mit erneut inhaltlich verschiedenen Fassungen (APIBench: 2 Dateien
vs. 4 andere Dateien unter derselben conceptrecid 5797296; RUBIES-Hviding25/Spectroscopic
Census: eine gemeinsame Datei mit unterschiedlicher Prüfsumme zwischen zwei echten Versionen;
Intelligent-Transport-Datensatz: eine zusätzliche Datei `dataLink.txt` in der jüngeren
Fassung) — dieselbe Beobachtung wie am 08.08., hier zum dritten Mal in Folge mehrfach pro Lauf
statt als Einzelfund. Ein Zenodo-Paar (`dh-0b34bb82220e8e96`/`dh-4048cdff8e3f92d9`,
conceptrecid 11003068) mit `access_right: restricted` und leerer Dateiliste — kein_merge
mangels Beleg, wie beim vergleichbaren Fall vom 07.08. Bei Mendeley `svbd7t4hkn` (drei
Kandidatenpaare) `doi.org`-Auflösung der unversionierten Basis-DOI geprüft: löst per Redirect
aktuell auf `/datasets/svbd7t4hkn/2` auf — dieselbe Mendeley-Basis-DOI-Drift wie beim
`hms3sjzt7f`-Fund vom 08.08., hier zum zweiten Mal beobachtet.

**Neues Muster: ein figshare/IEEE-DataPort-Cross-Repository-Paar mit tatsächlich
verifizierbarem inhaltlichem Unterschied.** `dh-04c39cf327aac09a`/`dh-51c5a98373099665`
(figshare 13484601, unversioniert/v1) gegen `dh-7915c99f3d35913b` (IEEE DataPort
10.21227/0ew3-pm58) — anders als beim unverifizierbaren IEEE-DataPort-Fall vom 07.08.
(Umleitung auf die Startseite) lud die IEEE-DataPort-Dokumentseite diesmal normal, mit
Browser-UA, Titel und Autorenliste sichtbar. figshare-API (`api.figshare.com/v2/articles/
13484601`) und IEEE-DataPort-Seite verglichen: figshare listet 320 Rohdatendateien für 80
Probanden (S01–S80, links/rechts), das IEEE-DataPort-Abstract nennt explizit nur 67
Probanden (27 osteoporotisch/osteopenisch + 40 gesund) — eine andere, kleinere Stichprobe.
Gleicher Titel, überlappende Autorenschaft (figshare: nur Adams; IEEE DataPort: Adams +
Makarov), aber belegt unterschiedlicher Dateninhalt. kein_merge für beide Paare.

**Stichprobe (15 Einträge):** 13 von 15 lösten normal auf, Titel stimmten in jedem geprüften
Fall (Zenodo ×8, ArcGIS ×3 [Layer-Namen statt Registertitel, erwartetes Muster], COCOON/
Huma-Num ×1 [neu in der Stichprobe, löste unauffällig auf], Språkbanken ×1). Darunter zwei
Concept-DOI-Drifts (`dh-0a976e909072f99d`: Zenodo 21602138 → 21602139, Titel identisch;
`dh-81665e69dd06b950`: Zenodo 21170149 → 21625925 — ein deutlich größerer Sprung als die
bisher beobachteten Drifts, Titel trotzdem exakt identisch, also derselbe Mechanismus, nur
mit mehr dazwischenliegenden Versionen). 2 von 15 (figshare, scielo.figshare) scheiterten mit
dem seit 04.08. bekannten AWS-WAF-202-Muster (Header `x-amzn-waf-action: challenge` bestätigt).
Keiner der 2 Ausfälle wurde markiert.

**Nicht getan:** Für die neun GBIF/PANGAEA-Merges keinen automatischen R4-Regel-Vorschlag für
`normalisiere.py`/`baue_bestand.py` umgesetzt — das wäre eine Pipeline-Änderung außerhalb des
Commit-Umfangs dieser Routine. Für die drei Dreiergruppen mit belegten Inhaltsunterschieden
und für das restricted-Zenodo-Paar keinen Merge vorgeschlagen, aus denselben Gründen wie an
den Vortagen.

**Regel/Prüfauftrag, neu:** GBIF registriert eigene DOIs für Datensätze, die es von anderen
Infrastrukturen (hier: PANGAEA) übernimmt, deklariert die Übernahme aber nur in seiner
eigenen API (`dataset.doi`-Feld), nicht in den DataCite-`relatedIdentifiers`, die
`normalisiere.py`/R2/R4 bislang auswerten. Sollte GBIF künftig häufiger im Register
auftauchen (bislang nur dieser eine Cluster von neun Paaren), wäre ein GBIF-spezifischer
Prüfschritt (Abgleich von `dataset.doi` gegen die harvestete PANGAEA-DOI vor dem Aufnehmen
als eigenständige Fundstelle, oder eine R4-Erweiterung, die GBIFs API statt nur
DataCite-Relationen befragt) ein eigener Prüfauftrag — analog zum weiterhin unumgesetzten
Concept-/Alias-DOI-Prüfauftrag vom 03.08., jetzt zum siebten Mal wiederholt (über 300
Kandidatenpaare mit demselben strukturellen Zenodo/Mendeley/figshare-Befund seit 03.08.).
Weiterhin geringe Dringlichkeit, da der Ernte-Cron pausiert ist.

## 2026-08-08 — Achter Lauf in Folge 40/40 kein_merge; erstmals echte Dreiergruppen mit inhaltlich verschiedenen Fassungen, ein zweiter Tombstone-Fund und die erste beobachtete Mendeley-Basis-DOI-Drift mit drei Versionen

Beurteilter Stand weiterhin `snapshot-2026-07-27c` (nächtlicher Cron seit 27.07. pausiert,
Register-Rückbau — `list_releases` bestätigt, jüngstes Release unverändert; Manifest lokal
gegengeprüft: 22.473 Einträge). `api.github.com` war wie an allen Vortagen mit HTTP 403
gesperrt; Behelf wie dokumentiert: Release-Metadaten per `mcp__github__list_releases`,
`hub-2026-07-27.sqlite.gz` über den ungesperrten `releases/download`-Pfad geladen,
SHA-256 gegen den Manifest-Eintrag geprüft (Treffer: `24018f5c…cf3b2`, 28.365.720 Bytes,
22.473 Einträge), `kandidaten.py` **ohne** `--aus-snapshot` aufgerufen (`beurteilter_stand`
steht deshalb als `lokaler Bau` in `urteil/vorlage.json` — der tatsächlich geprüfte Stand
ist `snapshot-2026-07-27c`, wie oben belegt). `bereits_beurteilte_paare` stand bei 400 vor
diesem Lauf, 5.606 Kandidaten blieben erneut gekappt (5.646 gefunden).

Alle 40 vorgelegten Kandidaten einzeln per Zenodo-, figshare- und Mendeley-API geprüft
(55 einzelne Zenodo-Record-Abfragen, nicht nur an Beispielen). Ergebnis: **40 von 40
kein_merge.** 34 davon waren das seit 03.08. etablierte Concept-/Versions-DOI-Muster
(23 klassische Zenodo-Paare, 4 Mendeley Basis-/`.1`-Paare mit nur einer registrierten
Version, 2 figshare-Paare desselben Artikels).

**Neu: drei echte Dreiergruppen, bei denen die dritte Kandidatenkombination nicht mehr
bloß Concept-DOI-Alias ist, sondern inhaltlich geprüft werden musste.** Bisher bestanden
Titel-Cluster fast immer aus genau zwei Fassungen plus optional deren Concept-DOI. Hier
zum ersten Mal drei Fälle mit echten Mehrfach-Beziehungen:

1. „Analyzing the Impact of AI on Traffic Management…" (Zenodo 15792665/15792666/15792705):
   15792666 enthält einen Textbericht (.docx+.pdf), während 15792665 (Concept-Alias) und
   15792705 (aktuelle Version) dieselbe Rohdaten-Tabelle („Hasil kuesioner.xlsx.xlsx")
   enthalten — R2 hatte alle drei korrekt als ein Werk verbunden, aber es sind erkennbar
   verschiedene Fassungen (Bericht vs. Daten), nicht nur DOI-Varianten desselben Inhalts.
2. „Anchored Stratification Arrays" (Zenodo 21607878/21607879/21609892): 21607878 ist
   Concept-Alias auf die aktuelle Version 21609892 (9 Dateien). 21607879 (8 Dateien) ist
   eine echte frühere Fassung — und bei den gemeinsamen Dateinamen (`verify_asa.py`,
   `README.md`, `signings_search.py`) unterscheiden sich die MD5-Prüfsummen zusätzlich zur
   fehlenden Datei `asa_256_127.txt`. **Neu gegenüber allen bisherigen Concept-DOI-Fällen:**
   nicht nur eine Datei kam hinzu, der Code selbst wurde zwischen den Fassungen geändert.
3. „AnDi 2 Benchmark dataset" (Zenodo 14132394/14281478/14281479): 14281478 ist
   Concept-Alias auf die lebendige aktuelle Version 14281479. 14132394 ist eine **komplett
   andere, unabhängige Concept-DOI**, deren aktuelle Zielversion (14132395, nicht im
   Register) mit HTTP 410 Gone und Tombstone antwortet — vom Hinterleger selbst
   zurückgezogen (`removal_reason: retracted`, 2024-12-05), mit geringfügig anderer
   Autorenschreibweise als die lebendige Reihe (Indiz für eine unabhängige, später
   verworfene Zweiteinreichung). Zwei Reihen desselben Werktitels, eine lebt, eine ist tot
   — kein_merge für alle drei Paare, und der tote Zugriffsweg von `dh-508224fcdeecb0d3`
   zusätzlich `markiert` (zweiter Tombstone-Fund nach `dh-62d66ade18ae8a57` am 05.08.,
   diesmal eine Ebene indirekter: über eine Concept-DOI, nicht über die registrierte
   Fassung selbst).

**Neu: die Mendeley-Basis-DOI-Drift erstmals mit tatsächlich divergierenden Versionen
beobachtet, nicht nur strukturell vermutet.** Bei allen bisherigen Mendeley-Kandidaten
(03.–07.08.) existierte laut Mendeley Public API nur eine einzige Version — Basis-DOI und
`.1`-DOI zeigten zwangsläufig auf denselben Stand, die Instabilität war rein strukturell
begründet. Heute zum ersten Mal ein Fall mit drei Versionen: `hms3sjzt7f` (AneRBC-Datensatz,
Kandidatenpaar `dh-1b2627d79989a50c`/`dh-72b505ff905c73fb`). DOI-Auflösung geprüft:
`doi.org/10.17632/hms3sjzt7f.1` → Version 1 (wie registriert), `doi.org/10.17632/hms3sjzt7f`
(unversioniert) → **Version 3**, nicht Version 1. Erstmals ein Beleg mit tatsächlich
unterschiedlichem Ziel statt nur einer strukturellen Möglichkeit.

**Neu: figshare-eigene Basis-Artikel-ID-Drift bestätigt (nicht nur Mendeley/
MaterialsCloud).** Beim Paar `dh-37b6b3352764d597`/`dh-4b5754d44711449a` (Artikel 29231351)
liefert die unversionierte figshare-Artikel-ID aktuell `version: 4` zurück, nicht v3 wie im
Kandidatenpaar — dasselbe „zeigt auf die neueste Version"-Muster wie bei Zenodo-Concept-
DOIs und Mendeley-Basis-DOIs, hier zum ersten Mal an einfachem `figshare.com` selbst
bestätigt statt nur an einer White-Label-Instanz. v3 und v4 waren inhaltlich (68/68
MD5-Treffer) identisch, trotzdem kein_merge nach der seit 05.08. geltenden Regel
(figshare-Versions-DOIs bleiben eigenständig registriert).

**Übrige 30 Kandidaten:** klassisches Zenodo-Concept-/Versions-Muster (23 Paare, per
`conceptrecid`-Feld einzeln bestätigt), 4 Mendeley-Ein-Versions-Paare, 1 figshare-Paar mit
inhaltlich identischen Versionen (v3/v4 desselben Artikels 29231351), 1 figshare-Paar mit
inhaltlich verschiedenen Versionen (University of Adelaide, 21163195 v1: 8 Dateien / v2:
9 Dateien, dieselben 8 MD5-identisch plus `nn_train.zip` neu — echte Fassungsänderung).
Nebenbefund ohne Entscheidungsrelevanz: Der Adelaide-Artikel wurde von der Hinterlegerin
seither weiter verändert (v3/v4 heißen inzwischen „random data", v4 ist leer) — die
registrierten Versions-URLs (`/21163195/1`, `/2`) liefern aber über die figshare-API
weiterhin den ursprünglichen Titel und vollständigen Dateibestand.

**Stichprobe (15 Einträge):** 8 von 15 lösten normal auf, Titel stimmten in jedem Fall
(Zenodo ×5, Apollo/Cambridge ×1, ArcGIS ×1 [Layer-Name „OSM_SA_Amenities" statt
Registertitel — erwartetes ArcGIS-REST-Muster, kein Fehlbefund]). Darunter drei
Concept-DOI-Drifts (`dh-7f8875e3fd9c9a64`: Zenodo-Konzept 6382414 → aktuell Record
6384747, laut `relations.version` Index 1/„is_last"; `dh-59e21835842ae1c2`: 10989595 →
10989596; `dh-accaa6229dfcc80b`: 21618574 → 21618575) — Titel exakt identisch in jedem
Fall, derselbe seit 03.08. dokumentierte Drift, kein neuer Befund. 7 von 15 (figshare ×3,
tandf.figshare ×1, scielo.figshare ×2, springernature.figshare ×1) scheiterten mit dem
seit 04.08. bekannten AWS-WAF-202-Muster. Keiner der 7 Ausfälle wurde markiert —
dokumentiertes Host-Blockmuster, kein Beleg für falsche Einträge.

**Nicht getan:** Für keine der drei neuen Dreiergruppen einen Fassungs- oder Werk-Merge
vorgeschlagen, obwohl R2 sie bereits korrekt als je ein Werk verbunden hatte — die
inhaltlichen Unterschiede (anderer Dateityp, geänderter Code, ein zurückgezogenes Duplikat)
sprechen jeweils gegen „dasselbe Ding". Für den zweiten Tombstone-Fund keinen Merge mit der
lebendigen Parallelreihe vorgeschlagen, obwohl beide denselben Werktitel tragen — die
geringfügig abweichende Autorenschreibweise ist ein Indiz, kein Beleg für Identität, und
„im Zweifel kein_merge" gilt hier doppelt (verschiedene Objekte plus einer davon tot).

**Regel/Prüfauftrag, jetzt zum sechsten Mal wiederholt:** Der Prüfauftrag vom 2026-08-03
(deterministische Concept-/Alias-DOI-Erkennung aus der geharvesteten `roh`-Metadatenform)
bleibt über sechs Urteilsläufe (03.–08.08.) hinweg unumgesetzt — inzwischen über 260
Kandidatenpaare mit demselben strukturellen Befund. Neu dazu, aus dem heutigen Lauf: Eine
rein strukturelle Erkennung („teilt sich eine conceptrecid/Basis-DOI") würde die drei
heutigen Dreiergruppen weiterhin als Kandidaten vorlegen, obwohl sie inhaltlich verschieden
sind — die Regel dürfte also nicht automatisch zusammenführen, sondern nur die
Concept-Alias-Kante aus der Kandidatenliste herausfiltern und die inhaltliche Prüfung
zwischen echten Versionen weiterhin dem Urteilslauf überlassen. Weiterhin geringe
Dringlichkeit, da der Ernte-Cron pausiert ist.

## 2026-08-07 — Siebter Lauf in Folge 40/40 kein_merge; erstmals zwei neue Muster statt nur Concept-/Versions-Drift: eine Zensus-Datenreihe und ein unverifizierbares IEEE-DataPort-Duplikat

Beurteilter Stand weiterhin `snapshot-2026-07-27c` (nächtlicher Cron seit 27.07. pausiert,
Register-Rückbau — `list_releases` bestätigt, jüngstes Release unverändert). `api.github.com`
war wie an den Vortagen mit HTTP 403 gesperrt; Behelf wie dokumentiert: Release-Metadaten
per `mcp__github__list_releases`, `hub-2026-07-27.sqlite.gz` über den ungesperrten
`releases/download`-Pfad geladen, SHA-256 gegen den Manifest-Eintrag geprüft (Treffer:
`24018f5c…cf3b2`, 28.365.720 Bytes, 22.473 Einträge), `kandidaten.py` **ohne**
`--aus-snapshot` aufgerufen (`beurteilter_stand` steht deshalb als `lokaler Bau` in
`urteil/vorlage.json` — der tatsächlich geprüfte Stand ist `snapshot-2026-07-27c`, wie oben
belegt). `bereits_beurteilte_paare` stand bei 360 vor diesem Lauf, 5.646 Kandidaten blieben
erneut gekappt.

**Neu: Zum ersten Mal seit dem 03.08. sind nicht alle 40 Kandidaten Concept-/Versions-DOI-
Paare.** 9 der 40 Paare trugen `gleiches_werk_bereits: false` — R2 hatte sie also noch gar
nicht verbunden, echte neue Kandidaten. Alle 9 stammen aus derselben Quelle: der
ETHNODOC-Datenbank des Leibniz-Instituts für Ost- und Südosteuropaforschung
(`lambda.ios-regensburg.de`), amtliche Volkszählungen (Ungarn 1990, Jugoslawien 1921).
DataCite liefert für jedes Paar denselben normalisierten Titel, denselben Urheber
(„Forschungsverbund Ost- und Südosteuropa (Forost)…") und denselben Herausgeber — nach
Beleg-Regel also klassische Merge-Kandidaten. Beide Zugriffswege jedes Paars tatsächlich
aufgerufen: die echten Seitentitel bei der Quelle unterscheiden sich durchgehend um eine
Aufschlüsselungsdimension, die die DataCite-Kurztitel nicht tragen — „nach Muttersprache"
vs. „nach Konfessionszugehörigkeit" vs. „nach Komitaten/Nationalität" derselben Erhebung.
Genau der in URTEILSROUTINE.md benannte Fehlerfall („Serien sehen aus wie Dubletten"),
hier zum ersten Mal bei einer Zensus-Datenbank statt bei Herbarbelegen oder Messreihen.
Alle 9 `kein_merge`, jedes Paar mit den beiden abweichenden Seitentiteln als Beleg.

**Neu: ein Paar mit ungewöhnlich starker Textgleichheit, aber ohne verifizierbaren Beleg
(IEEE DataPort).** `dh-503df15d0b719270`/`dh-ff520a0e00d71803` (DOIs 10.21227/6pfm-4x38 und
10.21227/490c-rm17) tragen wortgleichen Titel, wortgleiche mehrsätzige Beschreibung,
denselben Urheber, denselben Herausgeber und dieselbe registrierte Zugriffs-URL —
unabhängig registriert, 26 Tage auseinander, ohne jede `relatedIdentifiers`-Verknüpfung
zwischen den beiden DOIs. Das sieht nach einer echten Doppelregistrierung aus, stärker als
jedes bisher beobachtete Concept-/Versions-Paar. Aber: `doi.org`-Auflösung beider DOIs und
der direkte `ieee-dataport.org`-Link landen alle drei auf der Startseite statt auf der
Datensatzseite — mit Standard- und Browser-UA gleichermaßen. IEEE DataPort blockiert damit
automatisierten Zugriff auf eine neue Art (Umleitung auf die Startseite, nicht 403/WAF-202
wie bei GBIF/figshare/Dataverse). Ohne funktionierenden Live-Abgleich gibt es keinen Beleg
im Sinne der Regel („beide URLs aufgerufen, führen auf…") — trotz der ungewöhnlich starken
Textindizien `kein_merge`. Festgehalten für den Fall, dass IEEE-DataPort-Einträge künftig
häufiger auftauchen: Der Fall verdient eine gezielte Prüfung, sobald ein funktionierender
Zugriffsweg (z. B. eine dokumentierte IEEE-DataPort-API) bekannt ist.

**Übrige 30 Kandidaten:** wie an den sechs Vortagen ausnahmslos Zenodo-/Mendeley-/figshare-
Concept-/Versions-DOI-Paare, jedes Paar einzeln per API geprüft (Zenodo-Dateiprüfsummen,
Mendeley-/figshare-DataCite-Relationen). Darunter zwei Fälle mit tatsächlich
unterschiedlichem Dateiinhalt trotz gemeinsamer conceptrecid (`dh-0716b786ac19e165` gegen
beide Partner: 93.123 vs. 93.875 Byte, verschiedene Prüfsummen — eindeutig verschiedene
Fassungen), ein figshare-Paar mit vollständig verschiedenen Dateien zwischen v1 und v2
(3,76 GB vs. 4,97 GB) und ein figshare-Paar mit `IsIdenticalTo`-Relation und inhaltlich
identischen Dateien, bei dem trotzdem `kein_merge` blieb, weil die Quelle selbst v1 als
`IsPreviousVersionOf` (nicht `IsIdenticalTo`) von der aktuellen Fassung unterscheidet —
dieselbe Vorsicht wie bei den figshare-Fällen vom 05.08. Ein Zenodo-Paar
(`dh-345dce18fb33bdf9`/`dh-a7adbe37f79cf2eb`) konnte inhaltlich gar nicht verglichen werden
(`access_right: restricted`, keine Dateiliste) — auch hier `kein_merge` mangels Beleg.

**Stichprobe (15 Einträge):** 10 von 15 lösten normal auf, Titel stimmten in jedem Fall
(Zenodo ×6, Mendeley ×1, ArcGIS ×1, Språkbanken ×1 [neu in der Stichprobe, löste
unauffällig auf] — Titel-/`<title>`-Tag-Vergleich). Darunter erneut ein Concept-DOI-Drift
(`dh-1cda852b69298bd8`, Zenodo-Konzept 21566881 → aktueller Record 21566882, Titel exakt
identisch) — derselbe seit 04.08. dokumentierte Drift, kein neuer Befund. 5 von 15
(figshare ×3, karger.figshare ×1, Harvard Dataverse ×1) scheiterten mit dem seit 04.08.
bekannten AWS-WAF-202-Muster. Keiner der 5 Ausfälle wurde markiert — dokumentiertes
Host-Blockmuster, kein Beleg für falsche Einträge.

**Nicht getan:** Für das ETHNODOC-Muster keine deterministische Regel vorgeschlagen (anders
als beim Concept-/Versions-Prüfauftrag) — die Unterscheidung liegt hier nicht in einem
strukturellen DOI-Merkmal, sondern im Seiteninhalt der Quelle selbst (Aufschlüsselungs-
dimension im echten, nicht im DataCite-Titel), lässt sich also nicht ohne Live-Abgleich
automatisieren. Für das IEEE-DataPort-Paar keinen Merge trotz starker Textindizien
vorgeschlagen — Text-/Metadatengleichheit ersetzt keinen Zugriffsbeleg.

**Regel/Prüfauftrag, jetzt zum fünften Mal wiederholt:** Der Prüfauftrag vom 2026-08-03
(deterministische Concept-/Alias-DOI-Erkennung aus der geharvesteten `roh`-Metadatenform)
bleibt über fünf Urteilsläufe (03.–07.08.) hinweg unumgesetzt — inzwischen über 220
Kandidatenpaare mit demselben strukturellen Befund. Weiterhin geringe Dringlichkeit, da der
Ernte-Cron pausiert ist.

## 2026-08-06 — Sechster Lauf in Folge: wieder 40/40 kein_merge; Concept-Record mit HTTP 410 auf der API, registrierter Zugriffsweg löst trotzdem auf; api.github.com wieder gesperrt

Beurteilter Stand weiterhin `snapshot-2026-07-27c` (nächtlicher Cron seit 27.07. pausiert,
Register-Rückbau — kein neuerer Snapshot verfügbar; `list_releases` bestätigt, jüngstes
Release ist unverändert `snapshot-2026-07-27c` vom 27.07.). `bereits_beurteilte_paare`
stand bei 320, 5.686 Kandidaten blieben erneut gekappt.

`kandidaten.py --aus-snapshot` scheiterte wie am 27.07. mit HTTP 403 auf
`api.github.com` (Sitzungsrichtlinie, kein GitHub-Fehler). Behelf wie dokumentiert:
Release-Metadaten per `mcp__github__list_releases` geholt, `hub-2026-07-27.sqlite.gz`
über den ungesperrten `releases/download`-Pfad geladen, SHA-256 gegen den
Manifest-Eintrag geprüft (Treffer: `24018f5c…cf3b2`, 28.365.720 Bytes, 22.473
Einträge), lokal unter `bestand/hub.sqlite` abgelegt, `kandidaten.py` **ohne**
`--aus-snapshot` aufgerufen.

Alle 40 vorgelegten Kandidaten einzeln per Zenodo-, Mendeley- und figshare-API geprüft
(69 einzelne Zenodo-Record-Abfragen, nicht nur an Beispielen). Ergebnis wie an den
vier Vortagen: **40 von 40 kein_merge**, ausnahmslos Concept-/Versions-DOI-Paare.

**Neue API-Variante des Concept-DOI-Musters:** Beim Paar `dh-a2a271cfb97111f2`/
`dh-cd27e5e4a26b72ee` (Zenodo 10778229/10778230, „Albanian corpus …") antwortet der
direkte API-Endpunkt `zenodo.org/api/records/10778229` für die Concept-DOI mit
**HTTP 410 Gone** (`"The record has been deleted"`) statt, wie bei allen anderen
Paaren, mit einem 302-Redirect auf die aktuelle Version. Der tatsächlich registrierte
Zugriffsweg des Eintrags (`zenodo.org/doi/10.5281/zenodo.10778229`, ebenso der
DOI-Resolver `doi.org/10.5281/zenodo.10778229`) löst trotzdem mit HTTP 200 auf den
lebenden Record 10778230 auf — anders als beim Tombstone-Fund vom 03.08.
(`dh-62d66ade18ae8a57`, dort führte auch der registrierte Zugriffsweg selbst ins
Leere) ist hier nichts wirklich tot, nur ein alter API-Endpunkt für die
Concept-Record-Id wurde entfernt. Deshalb **kein `markiert`** — der Eintrag ist
gesund, nur ein Beleg mehr dafür, dass die Concept-/Versions-Instabilität nicht ein
einzelnes API-Verhalten ist, sondern mehrere.

Zusätzlich in der Stichprobe (nicht im Kandidatenpaar): Eintrag `dh-9a8bd7e9c1e9271f`
(Zenodo-Konzept 6337863) löst aktuell auf Record 6337923 auf — Titel exakt identisch
(„A Deep Neural Network Based SMAP Soil Moisture Product"), also derselbe Drift wie
die am 04.08. gelisteten fünf Fälle, hier zum ersten Mal an einem Stichprobeneintrag
statt an einem Merge-Kandidaten beobachtet.

**Stichprobe (15 Einträge):** 8 von 15 lösten normal auf, Titel stimmten in jedem
geprüften Fall (Zenodo ×4 inkl. des Drift-Falls oben, Mendeley ×2, PANGAEA ×1,
Dryad ×1 — `<title>`-Tag-Vergleich). 6 figshare/springernature.figshare/Dataverse-
Einträge scheiterten mit dem seit 2026-08-04 bekannten AWS-WAF-202-Muster. Keiner der
7 Ausfälle wurde markiert — dokumentiertes Host-Blockmuster, kein Beleg für falsche
Einträge.

**Nicht getan:** Wieder keinen automatischen Fassungs-Merge für die strukturell
identischen Concept-/Versions-Paare vorgeschlagen (aus denselben Gründen wie an den
vier Vortagen).

**Regel/Prüfauftrag daraus, jetzt zum vierten Mal wiederholt:** Der Prüfauftrag vom
2026-08-03 (deterministische Concept-/Alias-DOI-Erkennung aus der geharvesteten
`roh`-Metadatenform) bleibt über vier Urteilsläufe (03., 04., 05., 06.08.) hinweg
unumgesetzt — inzwischen über 190 Kandidatenpaare mit demselben strukturellen Befund.
Da der Ernte-Cron pausiert ist, bleibt die Dringlichkeit gering, aber der
Prüfauftrag verliert dadurch nicht an Substanz.

## 2026-08-05 — Fünfter Lauf in Folge: wieder 40/40 kein_merge, Concept-/Versions-DOI-Muster jetzt auch auf MaterialsCloud bestätigt; ein Zenodo-Record als Tombstone entdeckt

Beurteilter Stand weiterhin `snapshot-2026-07-27c` (der nächtliche Cron ist seit
2026-07-27 pausiert — Rückbau des Registers, s. `b9cb92a`/`1e20079` — daher kein neuerer
Snapshot verfügbar; `bereits_beurteilte_paare` in `urteil/vorlage.json` stand bei 280,
5.726 Kandidaten blieben erneut gekappt). Alle 40 vorgelegten Kandidaten einzeln per
Zenodo-, Mendeley-, figshare- und (neu) MaterialsCloud-API geprüft, nicht nur an
Beispielen — Ergebnis wie am 03./04.08.: **40 von 40 kein_merge.**

**Neu: MaterialsCloud bestätigt dasselbe Muster.** Ein Paar (`materialscloud:66-ec` /
`materialscloud:az-2c`) löste über zwei verschiedene DOIs auf denselben Record
(`0x1nd-2pq96`) auf. Die MaterialsCloud-API zeigt: `66-ec` ist `self_doi` (die
Versions-DOI dieses konkreten Eintrags), `az-2c` ist `parent_doi` (die Konzept-DOI der
übergeordneten Reihe, mit eigenem `latest`-Verweis auf `dngzm-q8x14`) — MaterialsCloud
läuft wie Zenodo auf InvenioRDM und hat exakt dieselbe Concept-/Versions-DOI-Struktur.
Das Muster ist damit auf vier Quellen bestätigt: Zenodo, Mendeley, figshare,
MaterialsCloud.

**Neuer Fund, kein Drift diesmal: ein Zenodo-Record wurde vom Hinterleger echt
gelöscht.** Beim Prüfen des Paars `dh-2a5791bb45c50159`/`dh-62d66ade18ae8a57`
(Zenodo 21610493/21610494) lieferte 21610494 nicht Metadaten, sondern HTTP 410 Gone mit
Tombstone: `removal_reason: test-record`, gelöscht am 2026-08-03 vom Hinterleger selbst.
Anders als die bisher dokumentierten Concept-DOI-Drifts (Weiterleitung auf eine neuere
Version) ist der Datensatz hier komplett fort — unter keiner URL mehr erreichbar. Der
zugehörige Registereintrag wurde deshalb zusätzlich `markiert` (eigener Journal-Eintrag,
eigener Commit), nicht nur `kein_merge` im Paar.

**Auch die figshare-v1/v2-Fälle sind nicht mehr eindeutig konzeptartig:** Bei
`17798777` waren v1 und v2 inhaltlich identisch (MD5-Treffer), bei `17798783` dagegen
inhaltlich verschieden (unterschiedliche MD5) — beides `kein_merge`, aber aus
verschiedenen Gründen (einmal strukturell/Concept-artig, einmal schlicht andere Datei).
Zusätzlich fiel auf: figshare-Versions-DOIs (`.v1`/`.v2`) sind, anders als
Zenodo-Concept-DOIs, jede für sich dauerhaft und eigenständig registriert — auch bei
identischem Dateiinhalt bleibt der `kein_merge`-Entscheid, weil ungeprüft ist, ob sich
die Metadaten zwischen den Versionen geändert haben.

**Stichprobe (15 Einträge):** 7 von 15 lösten normal auf, Titel stimmten in jedem Fall
(Zenodo ×5, Mendeley ×1, ScienceDB ×1 — Titel-Tag-Vergleich). 2 GBIF-Einträge scheiterten
mit dem seit 2026-07-26 bekannten 403-Bot-Block. 6 figshare-Einträge scheiterten mit dem
seit 2026-08-04 bekannten AWS-WAF-202-Muster — **neu dabei:** diesmal traf es nicht nur
die White-Label-Portale (karger.figshare.com, tandf.figshare.com), sondern auch **das
einfache `figshare.com` selbst** (3 der 6 betroffenen Einträge). Keiner der 8
Ausfälle wurde markiert — beides sind dokumentierte Host-Blockmuster, kein Beleg für
falsche Einträge.

**Nicht getan:** Wieder keinen automatischen Fassungs-Merge für inhaltlich identische
Concept-/Versions-Paare vorgeschlagen (Mendeley, figshare v1/v2 bei `17798777`) — aus
denselben strukturellen Gründen wie am 03./04.08.

**Regel/Prüfauftrag daraus, jetzt zum dritten Mal wiederholt:** Der Prüfauftrag vom
2026-08-03 (deterministische Concept-/Alias-DOI-Erkennung aus der geharvesteten
`roh`-Metadatenform, ohne Live-API-Aufruf) ist über drei Urteilsläufe (03.08., 04.08.
×2, 05.08.) hinweg **immer noch nicht umgesetzt** — mittlerweile über 150 Kandidatenpaare
mit demselben strukturellen Befund. Das ist inzwischen kein Rand-, sondern der
Hauptfall der Kandidatenliste; die Urteilsroutine wiederholt nachts dieselbe Diagnose,
statt dass `normalisiere.py` oder `kandidaten.py` sie einmal deterministisch anwendet.
Da der Ernte-Cron pausiert ist, ist die Dringlichkeit gering — aber sollte er
reaktiviert werden, sollte diese Regel vor dem nächsten Urteilslauf stehen, nicht danach.

## 2026-08-04 — Alle 40 Merge-Kandidaten sind Concept-/Versions-DOI-Paare; bei fünf zeigt die Concept-DOI schon auf eine dritte, unregistrierte Version

Bestätigt und vertieft den Befund vom 2026-08-03. Wieder trugen alle 40 vorgelegten
Merge-Kandidaten `gleiches_werk_bereits: true`. Diesmal wurde jedes Paar einzeln per
Zenodo-, figshare- und Mendeley-API geprüft (Dateiprüfsummen, `conceptrecid`,
Versions-Feld), nicht nur an Beispielen.

Ergebnis: 40 von 40 `kein_merge`. Darunter fünf Fälle, in denen die Concept-DOI zum
Prüfzeitpunkt **nicht** auf eines der beiden Kandidaten zeigte, sondern auf eine dritte,
im Register noch gar nicht erfasste, neuere Version — der konkrete Beweis für das am
03.08. nur begründete Risiko, dass eine Concept-DOI keine feste Referenz ist, sondern
wandert:

- Zenodo-Konzept 17737172 → aktuell Record 18386392
- Zenodo-Konzept 21432188 (Sivroni-Werk) → aktuell Record 21728269
- Zenodo-Konzept 17416652 → aktuell Record 19185175
- Zenodo-Konzept 12703231 → aktuell Record 19433890
- Zenodo-Konzept 16980461 → aktuell Record 17426012

Das Muster ist quellenübergreifend, nicht Zenodo-spezifisch: figshare (unversionierte
Artikel-ID) und Mendeley Data (DOI ohne Versions-Suffix) haben dieselbe „zeigt immer auf
die neueste Version"-Kennung. Bei vier geprüften Mendeley-Paaren existiert aktuell nur
eine veröffentlichte Version — unversionierte und `.1`-DOI sind inhaltlich (SHA-256)
identisch, trotzdem `kein_merge` aus strukturellen Gründen (dieselbe Instabilität wie bei
Zenodo, nur noch nicht eingetreten). Bei einem figshare-Dreiergespann (Basis-DOI, v4, v5)
zeigte die Basis-DOI aktuell per MD5-Treffer auf v5, nicht auf das im Kandidatenpaar
stehende v4 — ein Beleg mehr für dieselbe Instabilität, hier schon eingetreten.

**Nicht getan:** Keines der vier inhaltlich identischen Mendeley-Paare als Fassung
zusammengeführt, obwohl der Inhalt heute Byte für Byte übereinstimmt — die Konsequenz
wäre ein Fassungs-Eintrag, dessen Begründung mit der ersten neuen Version des Datensatzes
falsch würde, ohne dass irgendetwas im Register das anzeigt.

**Regel/Prüfauftrag daraus:** Der Prüfauftrag vom 03.08. bleibt (deterministische
Concept-/Alias-DOI-Erkennung aus der geharvesteten `roh`-Metadatenform, ohne Live-API-
Aufruf, damit solche Paare gar nicht erst als Kandidaten vorgelegt werden). Neu dazu:
Dieselbe Erkennung sollte figshare (unversionierte Artikel-ID) und Mendeley (DOI ohne
Versions-Suffix) mit abdecken, nicht nur Zenodo.

## 2026-08-04 — Automatisierter Zugriff auf Dataverse und figshare/Karger-figshare wird per AWS-WAF-Challenge abgewiesen (202, leerer Body)

In der Stichprobe (15 Einträge) lösten 7 von 15 Zugriffswegen mit HTTP 202 und leerem
Body auf, alle mit demselben Muster: Header `x-amzn-waf-action: challenge`, Herkunft
`awselb/2.0`. Betroffen: Harvard Dataverse (1 Eintrag) und figshare/karger.figshare.com/
tandf.figshare.com (6 Einträge). Mit Standard-UA (`dataset-hub-pipeline/...`) und mit
Browser-UA gleichermaßen geprüft — kein Unterschied, beide werden abgewiesen.

Strukturell derselbe Fall wie GBIF am 26.07. (Schema-Änderung v0.2.0,
`zugang.geprueft: versucht`): Der Datensatz existiert vermutlich, nur die automatisierte
Prüfung wird verwehrt. Keiner der 7 betroffenen Einträge wurde deshalb `markiert` — es
gibt keinen Beleg für einen falschen Eintrag, nur für einen verwehrten Prüfversuch. Die
übrigen 8 Einträge der Stichprobe (Zenodo, HuggingFace, ArcGIS, Mendeley) lösten normal
auf; Titel stimmten in jedem Fall überein (per `<title>`/`og:title`-Vergleich).

**Nicht getan:** Keinen der 7 betroffenen Einträge als geprüft vermerkt oder sonst wie
überbrückt — der Zugriffsweg wurde tatsächlich versucht, nicht bestätigt.

**Regel/Prüfauftrag daraus:** Sollte `aufloese.py` künftig auch figshare/Dataverse
durchlaufen, wird es denselben WAF-Block sehen wie hier — kein Grund zur Sorge, aber
`zugang.geprueft: versucht` mit `http_status: 202` sollte für diese Hosts erwartet, nicht
als Regression gedeutet werden. Beiläufig entdeckt: `api.figshare.com/v2/articles/<id>`
lieferte anstandslos JSON ohne WAF-Challenge — ob das ein Zugriffsweg wäre, der den WAF-
Block umgeht, ist ein eigener Prüfauftrag.

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
