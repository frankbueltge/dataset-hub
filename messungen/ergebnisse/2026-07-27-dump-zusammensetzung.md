# Messprotokoll — Woraus die 56,6 Millionen bestehen

**Datum:** 2026-07-27 · **Grundlage:** die lokal eingelesenen Rohernten des DataCite
Public Data File 2025 (56.620.404 Fundstellen vom Typ `dataset`) ·
**Stichprobe:** 400.000 Einträge aus 10 von 114 Teilen, gleichmäßig über den Bereich

Anlass: Frank fragte, ob geplant sei, 50 Millionen Unterseiten zu bauen (nein), und
schlug vor, „nur die letzten X Jahre" aufzunehmen. Die Messung hat beide Annahmen
korrigiert.

## 1. Jahresfilter reduziert fast nichts

| ab Jahr | Anteil | ≈ Einträge |
|---|---|---|
| 2024 | 61,7 % | 34.960.000 |
| 2022 | 66,7 % | 37.772.000 |
| 2020 | 85,0 % | 48.151.000 |
| 2015 | 92,1 % | 52.166.000 |

Der Bestand ist erdrückend jung. Selbst „nur ab 2024" lässt 35 Millionen übrig — als
Größenhebel taugt das Jahr nicht.

## 2. Der wirkliche Befund: zehn Herausgeber sind 95,8 %

| Anteil | ≈ Einträge | Herausgeber |
|---|---|---|
| **52,9 %** | 29.933.000 | National Institute for Fusion Science (NIFS) |
| 10,2 % | 5.772.000 | University of Southern California Digital Library |
| 9,9 % | 5.620.000 | UNITE Community |
| 8,6 % | 4.887.000 | The Global Biodiversity Information Facility |
| 7,0 % | 3.984.000 | PISCO MN |
| 3,7 % | 2.093.000 | Distributed System of Scientific Collections |
| 1,3 % | 708.000 | Edition Topoi |
| 1,0 % | 542.000 | Zenodo |
| 0,8 % | 466.000 | figshare |
| 0,4 % | 242.000 | Cambridge Crystallographic Data Centre |

543 verschiedene Herausgeber in der Stichprobe; die übrigen **rund 2,4 Millionen**
Einträge verteilen sich auf alle anderen.

## 3. Was das bedeutet

Diese Masse besteht nicht aus Datensätzen im gebräuchlichen Sinn, sondern aus
**Massenregistrierungen einzelner Beobachtungen**: ein DOI je Plasma-Experimentschuss,
je Pilz-Sequenz, je Fundmeldung eines Organismus, je Sammlungsbeleg. Jeder Eintrag ist
für sich korrekt vergeben — aber es ist die Granularitätsfrage aus dem Design (§1.3) in
ihrer schärfsten Form: **Ist ein einzelner Messschuss ein Datensatz?**

Nach dem Schema ist er es nicht auf derselben Ebene wie eine kuratierte Sammlung; er
entspricht eher `file` oder einer Beobachtung innerhalb einer Serie. Die Quelle sagt das
aber nicht — sie deklariert alles als `Dataset`.

Es erklärt zugleich rückwirkend zwei frühere Befunde: die 9.906 Merge-Kandidaten, die
sich als Herbarbelege entpuppten, und die Serien mit identischem Titel.

## 4. Folgerung (Vorschlag, Entscheidung offen)

Nicht wegwerfen, sondern **kennzeichnen**: Einträge von Herausgebern oberhalb einer
Massenschwelle bekommen ein Merkmal, das sie als Serien-Registrierung ausweist. Der
Nachweis bleibt vollständig — der Auftrag verlangt den größten maschinenlesbaren
Nachweis, nicht den bequemsten —, aber die Voreinstellung von Suche und Oberfläche
blendet sie aus. Wer Fusionsdaten sucht, findet sie; wer „offene Klimadaten" sucht,
ertrinkt nicht in 30 Millionen Experimentschüssen.

**Größenordnungen für den Bau:** ohne die zehn Massenherausgeber rund 2,4 Millionen
Einträge. Das ist eine Größe, mit der sich arbeiten lässt — sie übersteigt aber
weiterhin den jetzigen Bestandsbau, der alles im Arbeitsspeicher hält.
