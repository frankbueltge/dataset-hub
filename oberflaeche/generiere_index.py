#!/usr/bin/env python3
"""Erzeugt die statischen Daten der Oberfläche aus dem Bestand.

Die Oberfläche folgt den Daten: sie zeigt, was aufgenommen wurde — samt Lücken und
Prüfstand. Sie bestimmt nichts. Einzige Quelle ist bestand/hub.sqlite (derselbe
Bestand, den die Pipelines als Snapshot laden).
"""
import gzip
import json
import pathlib
import sqlite3
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "pipeline"))
from hub_lib import BESTAND, jetzt  # noqa: E402

ZIEL = pathlib.Path(__file__).resolve().parent / "public" / "daten"


def main():
    ZIEL.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(BESTAND / "hub.sqlite")
    db.row_factory = sqlite3.Row

    zeilen = []
    for r in db.execute("""
        SELECT id, werk_id, quelle, quell_id, granularitaet, titel, herausgeber,
               publikationsjahr, lizenz_id, zugang_url, zugang_geprueft,
               zugang_http_status, status
        FROM eintraege ORDER BY id
    """):
        zeilen.append({
            "i": r["id"], "w": r["werk_id"], "q": r["quelle"], "p": r["quell_id"],
            "g": r["granularitaet"], "t": r["titel"], "h": r["herausgeber"] or "",
            "j": r["publikationsjahr"], "l": r["lizenz_id"] or "",
            "u": r["zugang_url"], "v": r["zugang_geprueft"],
            "s": r["zugang_http_status"], "z": r["status"],
        })

    meta = dict(db.execute("SELECT schluessel, wert FROM meta"))
    fassungen = {}
    for r in db.execute("SELECT werk_id, COUNT(*) n FROM eintraege GROUP BY werk_id HAVING n>1"):
        fassungen[r["werk_id"]] = r["n"]

    manifeste = []
    for m in sorted((pathlib.Path(__file__).resolve().parent.parent
                     / "fundstellen" / "manifeste").glob("*.json")):
        d = json.loads(m.read_text())
        manifeste.append({k: d.get(k) for k in
                          ("quelle", "seit", "bis", "records", "vollstaendig")})

    ablehnungen = [dict(r) for r in db.execute(
        "SELECT grund, COUNT(*) n FROM ablehnungen GROUP BY grund ORDER BY n DESC")]
    ausfaelle = [dict(r) for r in db.execute(
        "SELECT datum, quelle, fehler, kontext FROM ausfaelle ORDER BY datum DESC LIMIT 50")]
    db.close()

    (ZIEL / "eintraege.json").write_text(json.dumps(zeilen, ensure_ascii=False,
                                                    separators=(",", ":")))
    with gzip.open(ZIEL / "eintraege.json.gz", "wt", encoding="utf-8") as f:
        json.dump(zeilen, f, ensure_ascii=False, separators=(",", ":"))

    (ZIEL / "meta.json").write_text(json.dumps({
        "erzeugt": jetzt(),
        "schema_version": meta.get("schema_version"),
        "gebaut_am": meta.get("gebaut_am"),
        "zaehler": {k: int(meta.get(k, 0)) for k in
                    ("eintraege", "werke", "fundstellen", "abgelehnt_gesamt",
                     "aufgeloest_versucht", "aufgeloest_bestaetigt")},
        "mehrfassungs_werke": len(fassungen),
        "quellfenster": manifeste,
        "ablehnungen": ablehnungen,
        "ausfaelle": ausfaelle,
    }, ensure_ascii=False, indent=2))

    roh = (ZIEL / "eintraege.json").stat().st_size
    komp = (ZIEL / "eintraege.json.gz").stat().st_size
    print(f"{len(zeilen)} Einträge → {ZIEL}")
    print(f"  eintraege.json     {roh / 1e6:.2f} MB")
    print(f"  eintraege.json.gz  {komp / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
