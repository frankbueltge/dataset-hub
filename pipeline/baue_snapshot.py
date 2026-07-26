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

    assets = [sqlite_gz]
    quellfenster = []
    for m in sorted(MANIFESTE.glob("*.json")):
        manifest = json.loads(m.read_text())
        quellfenster.append({k: manifest.get(k) for k in
                             ("lauf", "quelle", "seit", "bis", "records", "vollstaendig")})
        rohdatei = MANIFESTE.parent / manifest["datei"]
        if rohdatei.exists():
            assets.append(rohdatei)

    manifest = {
        "tag": tag,
        "schema_version": meta.get("schema_version"),
        "gebaut_am": jetzt(),
        "zaehler": {k: meta.get(k) for k in
                    ("eintraege", "werke", "fundstellen", "abgelehnt_gesamt",
                     "aufgeloest_versucht", "aufgeloest_bestaetigt")},
        "quellfenster": quellfenster,
        "assets": [{"name": a.name, "sha256": sha256_datei(a), "bytes": a.stat().st_size}
                   for a in assets],
    }
    manifest_pfad = SNAPSHOTS / f"{tag}.manifest.json"
    manifest_pfad.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    print("\nAssets für das Release:")
    for a in assets:
        print(f"  {a}")
    return manifest


if __name__ == "__main__":
    main()
