#!/usr/bin/env python3
"""Snapshot-Bau: bestand/hub.sqlite → komprimiertes Release-Asset + Manifest.

Das Manifest (Zähler, SHA-256 aller Assets, Quellfenster, schema_version) wird in
Git committet (snapshots/); die großen Dateien hängen am getaggten GitHub-Release.
Der Snapshot-Vertrag IST die Abfrage-API der Ökologie.
"""
import gzip
import json
import shutil
import sqlite3

from hub_lib import BESTAND, MANIFESTE, SNAPSHOTS, heute, jetzt, sha256_datei

BUILD = SNAPSHOTS / "build"


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    db_pfad = BESTAND / "hub.sqlite"
    db = sqlite3.connect(db_pfad)
    meta = dict(db.execute("SELECT schluessel, wert FROM meta"))
    db.close()

    tag = f"snapshot-{heute()}"
    sqlite_gz = BUILD / f"hub-{heute()}.sqlite.gz"
    with open(db_pfad, "rb") as f_in, gzip.open(sqlite_gz, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)

    # Die Oberflächen-Daten reisen als Release-Dateien mit: die Site holt sie beim Bauen,
    # statt sie in ihrer Git-Historie mitzuschleppen (14 MB je Stand, nächtlich wachsend).
    # Erzeugt werden sie von oberflaeche/generiere_index.py; fehlen sie, wird das vermerkt
    # statt stillschweigend ein Snapshot ohne Oberflächendaten zu veröffentlichen.
    oberflaeche = SNAPSHOTS.parent / "oberflaeche" / "public" / "daten"
    fehlend = []
    for name in ("eintraege.json", "meta.json", "details.json", "werke.json", "liste.json"):
        quelle = oberflaeche / name
        if quelle.exists():
            ziel = BUILD / name
            with open(quelle, "rb") as f_in, gzip.open(str(ziel) + ".gz", "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        else:
            fehlend.append(name)

    assets = [sqlite_gz] + sorted(BUILD.glob("*.json.gz"))
    quellfenster, fehlende_rohernten = [], []
    for m in sorted(MANIFESTE.glob("*.json")):
        manifest = json.loads(m.read_text())
        # Ein Erntefenster darf nur behauptet werden, wenn seine Rohernte beim Bau
        # tatsächlich vorlag. Am 27.07. war das nicht so: Die Manifeste liegen in Git,
        # die Rohernten nur in den Releases — der nächtliche Lauf sah auf fremdem
        # Rechner nur seine eigene Ernte und baute 12.915 statt 17.327 Einträge, während
        # das Manifest weiter alle sieben Fenster auswies. Ein Snapshot, der mehr
        # behauptet, als in ihm steckt, ist schlimmer als ein kleiner Snapshot.
        dateien = manifest.get("dateien") or ([manifest["datei"]] if manifest.get("datei") else [])
        vorhanden = [d for d in dateien if (MANIFESTE.parent / d).exists()]
        eintrag = {k: manifest.get(k) for k in
                   ("lauf", "quelle", "seit", "bis", "records", "vollstaendig")}
        eintrag["rohernte_im_bau"] = bool(vorhanden) and len(vorhanden) == len(dateien)
        if not eintrag["rohernte_im_bau"]:
            fehlende_rohernten.append(manifest.get("lauf"))
        quellfenster.append(eintrag)
        assets.extend(MANIFESTE.parent / d for d in vorhanden)

    manifest = {
        "tag": tag,
        "schema_version": meta.get("schema_version"),
        "gebaut_am": jetzt(),
        # "eintraege" ist der GANZE Bestand — er steckt vollständig in hub-*.sqlite.gz,
        # dem Haupt-Asset. "kernbestand" ist die kuratierte Auswahl (Neufassung §4,
        # Stufe 2); NUR sie steckt in den mitreisenden eintraege.json/details.json, die
        # die Website baut. Beide Zahlen stehen hier, damit niemand die kleinere für
        # den Bestand hält oder die größere für das, was die Site zeigt.
        "zaehler": {k: meta.get(k) for k in
                    ("eintraege", "werke", "fundstellen", "abgelehnt_gesamt",
                     "aufgeloest_versucht", "aufgeloest_bestaetigt",
                     "kernbestand", "kernbestand_regel", "kernbestand_urteil",
                     "kernbestand_grenzfaelle_offen")},
        "quellfenster": quellfenster,
        "assets": [{"name": a.name, "sha256": sha256_datei(a), "bytes": a.stat().st_size}
                   for a in assets],
    }
    if fehlend:
        manifest["oberflaechendaten_fehlen"] = fehlend
    if fehlende_rohernten:
        manifest["rohernten_nicht_im_bau"] = fehlende_rohernten
        manifest["hinweis"] = (
            f"{len(fehlende_rohernten)} Erntelauf/-läufe sind in diesem Bestand NICHT "
            "enthalten — ihre Rohernten lagen beim Bau nicht vor. Die Zähler beziehen "
            "sich nur auf das tatsächlich Gebaute.")
    manifest_pfad = SNAPSHOTS / f"{tag}.manifest.json"
    manifest_pfad.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    print("\nAssets für das Release:")
    for a in assets:
        print(f"  {a}")
    return manifest


if __name__ == "__main__":
    main()
