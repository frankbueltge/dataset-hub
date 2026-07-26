#!/usr/bin/env python3
"""Frage das Dataset Register — eine Datei, nur Standardbibliothek, überall lauffähig.

Gedacht für die Praxen der Ökologie: Ihre Verfassungen verlangen, dass jede Tatsachen-
behauptung an einer *tatsächlich abrufbaren* Quelle hängt und fremdes Material nur
verwendet wird, wenn es offen lizenziert ist. Genau das führt das Register mit — samt
Prüfstand, ob der Zugriffsweg wirklich antwortet.

    python3 frage_register.py --suche "climate temperature" --geprueft --offen
    python3 frage_register.py --suche "election" --lizenz cc0 --format json

Der Snapshot wird einmal geholt und lokal zwischengespeichert (~20 MB); danach laufen
Abfragen offline in Millisekunden. `--frisch` erzwingt einen neuen Abruf.

WAS DAS REGISTER NICHT IST: vollständig. Es erntet erst seit dem 26.07.2026 und weist
seine Lücken selbst aus (`--stand`). Findet es nichts, heißt das „nicht in diesem
Bestand" — nicht „gibt es nicht". Fehlt euch etwas, schreibt es in
`bedarf/offen.md` des Registers; daraus werden neue Quellen.
"""
import argparse
import gzip
import json
import os
import pathlib
import shutil
import sqlite3
import sys
import urllib.request

REPO = "frankbueltge/dataset-hub"
UA = "dataset-register-abfrage/1.0"
CACHE = pathlib.Path(os.environ.get("REGISTER_CACHE",
                                    pathlib.Path.home() / ".cache" / "dataset-register"))


def hole(url: str, roh=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "application/vnd.github+json"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read() if roh else json.loads(r.read())


def snapshot(frisch: bool) -> pathlib.Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    db = CACHE / "hub.sqlite"
    stand = CACHE / "stand.json"
    if db.exists() and not frisch:
        return db

    releases = [r for r in hole(f"https://api.github.com/repos/{REPO}/releases")
                if r["tag_name"].startswith("snapshot-") and not r["draft"]]
    if not releases:
        sys.exit("Kein Snapshot-Release gefunden — das ist ein Ausfall, kein leeres Register.")
    rel = sorted(releases, key=lambda r: r["tag_name"], reverse=True)[0]
    asset = next((a for a in rel["assets"] if a["name"].endswith(".sqlite.gz")), None)
    if not asset:
        sys.exit(f"Im Release {rel['tag_name']} fehlt der Bestand (*.sqlite.gz).")

    print(f"… hole {rel['tag_name']} ({asset['size'] / 1e6:.0f} MB, einmalig)",
          file=sys.stderr)
    gepackt = hole(asset["browser_download_url"], roh=True)
    db.write_bytes(gzip.decompress(gepackt))
    stand.write_text(json.dumps({"tag": rel["tag_name"], "asset": asset["name"]}))
    return db


def stand_zeigen(db: pathlib.Path):
    c = sqlite3.connect(db)
    meta = dict(c.execute("SELECT schluessel, wert FROM meta"))
    tag = json.loads((CACHE / "stand.json").read_text())["tag"] if (CACHE / "stand.json").exists() else "?"
    print(f"Stand: {tag} · Schema {meta.get('schema_version')} · gebaut {meta.get('gebaut_am')}")
    print(f"  {int(meta.get('eintraege', 0)):,} Einträge · {int(meta.get('werke', 0)):,} Werke")
    print(f"  Zugriffswege: {int(meta.get('aufgeloest_bestaetigt', 0)):,} bestätigt "
          f"von {int(meta.get('aufgeloest_versucht', 0)):,} geprüft")
    print("  Quellen:")
    for q, n in c.execute("SELECT quelle, COUNT(*) FROM eintraege GROUP BY quelle ORDER BY 2 DESC"):
        print(f"    {q:<14} {n:>8,}")
    print("  Verworfen (mit Grund):")
    for g, n in c.execute("SELECT grund, COUNT(*) FROM ablehnungen GROUP BY grund ORDER BY 2 DESC"):
        print(f"    {g:<32} {n:>8,}")
    print("\n  Das Register erntet ab Aufsetzzeitpunkt vorwärts — der Altbestand fehlt")
    print("  noch. Kein Treffer heißt „nicht in diesem Bestand\", nicht „gibt es nicht\".")
    c.close()


def suchen(db, begriffe, lizenz, nur_geprueft, nur_offen, quelle, jahr_ab, limit):
    c = sqlite3.connect(db)
    c.row_factory = sqlite3.Row
    wo, args = [], []
    if begriffe:
        wo.append("e.id IN (SELECT id FROM eintraege_fts WHERE eintraege_fts MATCH ?)")
        args.append(" ".join(begriffe))
    if nur_geprueft:
        wo.append("e.zugang_geprueft IN ('landing','download')")
    if nur_offen:
        # „offen" heißt hier: die Quelle nennt eine Lizenz, die Weiterverwendung erlaubt.
        # Ohne Angabe gilt nichts als offen — nicht erfinden, was nicht dasteht.
        wo.append("(e.lizenz_id LIKE 'cc0%' OR e.lizenz_id LIKE 'cc-by%' "
                  "OR e.lizenz_id LIKE 'pddl%' OR e.lizenz_id LIKE 'odbl%')")
    if lizenz:
        wo.append("lower(e.lizenz_id) LIKE ?")
        args.append(f"%{lizenz.lower()}%")
    if quelle:
        wo.append("e.quelle = ?")
        args.append(quelle)
    if jahr_ab:
        wo.append("e.publikationsjahr >= ?")
        args.append(jahr_ab)
    sql = ("SELECT e.titel, e.herausgeber, e.publikationsjahr, e.lizenz_id, e.zugang_url, "
           "e.zugang_geprueft, e.zugang_http_status, e.quelle, e.quell_id, e.id FROM eintraege e")
    if wo:
        sql += " WHERE " + " AND ".join(wo)
    sql += " ORDER BY (e.zugang_geprueft IN ('landing','download')) DESC, e.publikationsjahr DESC LIMIT ?"
    args.append(limit)
    treffer = [dict(r) for r in c.execute(sql, args)]
    c.close()
    return treffer


PRUEFSTAND = {
    "landing": "Zugriff bestätigt",
    "download": "Zugriff bestätigt",
    "versucht": "geprüft, nicht bestätigt",
    "none": "ungeprüft",
}


def main():
    p = argparse.ArgumentParser(description="Frage das Dataset Register der Ökologie.")
    p.add_argument("--suche", nargs="*", default=[], help="Wörter in Titel/Beschreibung")
    p.add_argument("--lizenz", help="Teilstring, z. B. cc0, cc-by")
    p.add_argument("--quelle", help="datacite, arcgis, huggingface …")
    p.add_argument("--jahr-ab", type=int)
    p.add_argument("--geprueft", action="store_true",
                   help="nur Einträge mit per HTTP bestätigtem Zugriffsweg")
    p.add_argument("--offen", action="store_true",
                   help="nur Einträge mit ausdrücklich offener Lizenz")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--format", choices=("text", "json"), default="text")
    p.add_argument("--stand", action="store_true", help="zeigt Umfang und Lücken")
    p.add_argument("--frisch", action="store_true", help="Snapshot neu holen")
    a = p.parse_args()

    db = snapshot(a.frisch)
    if a.stand:
        stand_zeigen(db)
        return

    treffer = suchen(db, a.suche, a.lizenz, a.geprueft, a.offen, a.quelle, a.jahr_ab, a.limit)
    if a.format == "json":
        print(json.dumps(treffer, ensure_ascii=False, indent=2))
        return

    if not treffer:
        print("Kein Treffer in diesem Bestand. Das ist keine Aussage über die Welt —")
        print("das Register erntet erst seit dem 26.07.2026 (siehe --stand).")
        return
    for t in treffer:
        print(f"\n{t['titel']}")
        zeile = " · ".join(x for x in (t["herausgeber"] or "", str(t["publikationsjahr"] or ""),
                                       t["lizenz_id"] or "Lizenz: keine Angabe") if x)
        print(f"  {zeile}")
        stand = PRUEFSTAND.get(t["zugang_geprueft"], t["zugang_geprueft"])
        if t["zugang_geprueft"] == "versucht":
            stand += f" (HTTP {t['zugang_http_status']} — bei 403 meist Bot-Schutz, kein toter Link)"
        print(f"  {stand}")
        print(f"  {t['zugang_url']}")
        print(f"  {t['quelle']}:{t['quell_id']}")
    print(f"\n{len(treffer)} Treffer (Grenze {a.limit}). Zitierhinweis: die Zugriffs-URL steht")
    print("wörtlich so in der Quelle — sie wurde nie konstruiert.")


if __name__ == "__main__":
    main()
