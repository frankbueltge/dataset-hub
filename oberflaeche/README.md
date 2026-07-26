# Oberfläche

Statische Suchoberfläche über den Bestand. **Die Oberfläche folgt den Daten:** Sie zeigt,
was aufgenommen wurde — samt Prüfstand, leeren Feldern und ausgewiesener Bestandslücke.
Sie bestimmt nicht, was aufgenommen wird, und ergänzt nichts, was die Quelle nicht sagt.

Kein Build-Schritt, kein Framework, keine externen Requests: eine HTML-Datei, ein
Stylesheet, ein Skript und zwei generierte JSON-Dateien.

## Erzeugen und lokal ansehen

```bash
cd oberflaeche
python3 generiere_index.py          # bestand/hub.sqlite → public/daten/*.json
cd public && python3 -m http.server 8765
# http://127.0.0.1:8765/
```

`generiere_index.py` liest denselben Bestand, den auch der Snapshot enthält — eine
Wahrheit, zwei Türen (Menschen hier, Pipelines über `SNAPSHOT-API.md`).

## Was die Marken bedeuten

| Marke | Bedeutung |
|---|---|
| **Zugriff bestätigt** | Zugriffsweg per HTTP aufgelöst, 2xx |
| **geprüft, nicht bestätigt (Status)** | aufgelöst, aber der Host antwortete anders — 403 ist meist Bot-Schutz, kein toter Link |
| **Zugriff ungeprüft** | noch nicht aufgelöst (Auflösung läuft als nächtliches Budget) |
| **Eintrag ungeprüft** | automatisch aufgenommen, inhaltlich nicht gesichtet |
| **Lizenz: keine Angabe** | die Quelle nennt keine — die Lücke bleibt sichtbar, statt gefüllt zu werden |

Auch „kein Treffer" sagt, was es heißt: nichts im *aufgenommenen Bestand* — keine
Aussage über die Welt.

## Stand und offene Punkte

Erste Fassung, lokal getestet (Suche, Filter, Leerfall, Nachladen). Noch offen:
Veröffentlichung (Cloudflare Pages, gemeinsam mit der Site zu entscheiden),
Einzelansicht je Eintrag mit Zitiervorschlag, Werk-/Fassungs-Ansicht.
Bei wachsendem Bestand löst eine Such-API (Worker + D1 aus demselben Snapshot) den
mitgelieferten Index ab — die Grenze liegt erfahrungsgemäß im niedrigen
sechsstelligen Bereich an Einträgen.
