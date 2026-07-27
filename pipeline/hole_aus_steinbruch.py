#!/usr/bin/env python3
"""Abbau aus dem Steinbruch: gezielt aus dem DataCite-Bulk holen, was das
Relevanzkriterium entscheidet.

Seit der Neufassung des Registerzwecks (frankbueltge.de →
docs/design/2026-07-27-register-neufassung.md, §5) ist der Bulk **Rohmaterial, kein
Bestand**. Er wird nie als Ganzes eingelesen. Dieses Skript liest ihn im Strom,
wendet beide Stufen an und schreibt NUR die Treffer als gewöhnliche Fundstellen-Datei
heraus — von dort übernimmt die normale Pipeline (baue_bestand.py) unverändert.

## Was mitkommt — und was nicht

Mitgenommen wird, was der Kernbestand-Sieb per **Regel** entscheidet: ein Begriff im
Titel, der für sich schon trägt. **Grenzfälle bleiben liegen.** Gemessen am 27.07.
(Stichprobe von 1,5 Mio. Einträgen, hochgerechnet) stünden ihnen rund 124.000 Einträge
gegenüber — ein Urteilsvorrat, den niemand abarbeitet, und 124.000 Einträge, die den
Bestand um ein Vielfaches aufblähten, ohne je sichtbar zu werden. Wer sie will, holt
sie mit `--auch-grenzfaelle`; die Voreinstellung lässt sie im Steinbruch.

Das ist eine Kappung, und sie wird beziffert: das Manifest führt `grenzfaelle_gesehen`.

Nur Standardbibliothek. Kein Netzzugriff — das Rohmaterial liegt lokal.
"""
import argparse
import collections
import gzip
import json
import multiprocessing
import pathlib
import sys

from hub_lib import MANIFESTE, FUNDSTELLEN, jetzt, sha256_datei
from kernbestand import siebe
from normalisiere import GRANULARITAET, normalisiere_datacite
from relevanz import Massenherausgeber, lizenz_benannt

ADAPTER_VERSION = "0.1.0"
STEINBRUCH = pathlib.Path(__file__).resolve().parent.parent / "steinbruch"


def _knapper_eintrag(roh: dict) -> dict:
    """Nur die drei Felder, die Stufe 1 braucht — direkt aus dem Rohdatensatz.

    Grund: `normalisiere_datacite` baut je Datensatz einen vollständigen Eintrag mit
    Urhebern, Relationen, Identifikatoren und Daten. Gemessen scheitern 97 % der
    Bulk-Datensätze schon an Stufe 1; sie erst vollständig aufzubauen und dann
    wegzuwerfen ist der teuerste Weg zum selben Ergebnis.

    Die GATTER sind bewusst dieselben Funktionen wie im Bestandsbau
    (`massenherausgeber.trifft`, `lizenz_benannt`) — nur die Feldentnahme steht hier
    doppelt. Sie ist absichtlich wörtlich aus `normalisiere_datacite` übernommen; wer
    dort etwas ändert, ändert es auch hier.
    """
    pub = roh.get("publisher")
    herausgeber = (pub.get("name") if isinstance(pub, dict) else pub) or ""
    typ_roh = (roh.get("types") or {}).get("resourceTypeGeneral") or ""
    lizenz_id = ""
    for r in roh.get("rightsList") or []:
        lizenz_id = (r.get("rightsIdentifier") or "").strip()
        if lizenz_id:
            break
    return {
        "herausgeber": herausgeber.strip() if isinstance(herausgeber, str) else "",
        "granularitaet": GRANULARITAET.get(typ_roh, "dataset" if typ_roh else ""),
        "lizenz": {"id": lizenz_id, "roh": []},
    }


def _teil_abbauen(auftrag):
    """Ein Bulk-Teil im Strom lesen; Treffer als Zeilen zurückgeben.

    Läuft im eigenen Prozess: die Massenherausgeber-Liste wird dort neu geladen
    (billig) statt über die Prozessgrenze gereicht.
    """
    pfad_str, auch_grenzfaelle = auftrag
    pfad = pathlib.Path(pfad_str)
    massenherausgeber = Massenherausgeber.lade()
    treffer = []
    zaehler = collections.Counter()
    with gzip.open(pfad, "rt", encoding="utf-8") as f:
        for zeile in f:
            zaehler["gelesen"] += 1
            try:
                fund = json.loads(zeile)
            except Exception:
                zaehler["kaputte_zeilen"] += 1
                continue
            # Stufe 1 vorweg und auf dem Rohdatensatz: was ohnehin nicht in den
            # Bestand darf, wird weder normalisiert noch gesiebt.
            knapp = _knapper_eintrag(fund.get("roh") or {})
            if massenherausgeber.trifft(knapp):
                zaehler["massenregistrierung"] += 1
                continue
            if not lizenz_benannt(knapp):
                zaehler["lizenz_nicht_benannt"] += 1
                continue
            eintrag = normalisiere_datacite(fund)
            stufe, _ = siebe(eintrag)
            if stufe == "regel" or (auch_grenzfaelle and stufe == "grenzfall"):
                zaehler[f"genommen_{stufe}"] += 1
                treffer.append(zeile.rstrip("\n"))
            elif stufe == "grenzfall":
                zaehler["grenzfaelle_gesehen"] += 1
    return {"datei": pfad.name, "zaehler": dict(zaehler), "treffer": treffer}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--steinbruch", default=str(STEINBRUCH),
                   help="Ordner mit den Bulk-Teilen (*.jsonl.gz)")
    p.add_argument("--auch-grenzfaelle", action="store_true",
                   help="Grenzfälle mitnehmen (Voreinstellung: nein, siehe Modulkopf)")
    args = p.parse_args()

    ordner = pathlib.Path(args.steinbruch)
    teile = sorted(ordner.glob("*.jsonl.gz"))
    if not teile:
        sys.exit(f"kein Rohmaterial in {ordner} — nichts abzubauen.")
    print(f"{len(teile)} Teile, {sum(t.stat().st_size for t in teile) / 1e9:.1f} GB gz")

    lauf = f"steinbruch-{jetzt().replace('-', '').replace(':', '')}"
    FUNDSTELLEN.mkdir(exist_ok=True)
    MANIFESTE.mkdir(parents=True, exist_ok=True)
    # Kein "-dump-" im Namen: das Ergebnis IST eine Fundstelle und soll vom
    # Bestandsbau gelesen werden (der überspringt nur Bulk-Rohmaterial).
    datei = FUNDSTELLEN / f"{lauf}.jsonl.gz"

    gesamt = collections.Counter()
    prozesse = max(1, (multiprocessing.cpu_count() or 2) - 2)
    with gzip.open(datei, "wt", encoding="utf-8") as aus:
        with multiprocessing.Pool(prozesse) as pool:
            auftraege = [(str(t), args.auch_grenzfaelle) for t in teile]
            for i, ergebnis in enumerate(pool.imap_unordered(_teil_abbauen, auftraege), 1):
                for zeile in ergebnis["treffer"]:
                    aus.write(zeile + "\n")
                gesamt.update(ergebnis["zaehler"])
                print(f"  [{i}/{len(teile)}] {ergebnis['datei']}: "
                      f"{len(ergebnis['treffer'])} genommen", flush=True)

    records = gesamt.get("genommen_regel", 0) + gesamt.get("genommen_grenzfall", 0)
    manifest = {
        "lauf": lauf, "quelle": "datacite", "adapter_version": ADAPTER_VERSION,
        "verfahren": ("Abbau aus dem Steinbruch: DataCite Public Data File 2025, "
                      "gefiltert durch Relevanzkriterium Stufe 1 + Kernbestand-Sieb"),
        "seit": None, "bis": jetzt(), "records": records,
        # Ein Abbau ist NIE vollständig im Sinne des Quellfensters — er nimmt eine
        # Auswahl. Das als `vollstaendig: true` auszuweisen wäre eine Lüge im Manifest.
        "vollstaendig": False,
        "gelesen": gesamt.get("gelesen", 0),
        "abgewiesen_massenregistrierung": gesamt.get("massenregistrierung", 0),
        "abgewiesen_lizenz_nicht_benannt": gesamt.get("lizenz_nicht_benannt", 0),
        "genommen_regel": gesamt.get("genommen_regel", 0),
        "genommen_grenzfall": gesamt.get("genommen_grenzfall", 0),
        # Sichtbare Kappung: so viele Grenzfälle sind im Steinbruch geblieben.
        "grenzfaelle_gesehen": gesamt.get("grenzfaelle_gesehen", 0),
        "kaputte_zeilen": gesamt.get("kaputte_zeilen", 0),
        "datei": datei.name, "sha256": sha256_datei(datei),
    }
    (MANIFESTE / f"{lauf}.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return manifest


if __name__ == "__main__":
    main()
