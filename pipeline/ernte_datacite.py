#!/usr/bin/env python3
"""Ernte-Adapter DataCite (inkrementell): updated-Fenster, Cursor-Paginierung.

Schreibt Fundstellen wörtlich (roh = attributes) als JSONL.gz plus Manifest mit
Zähler, Zeitfenster, SHA-256 und Vollständigkeits-Flag. Ein Abbruch wird als
Ausfall registriert und im Manifest sichtbar — nie stillschweigend.
"""
import argparse
import datetime
import gzip
import json

from hub_lib import (FUNDSTELLEN, MANIFESTE, hole, jetzt, normalisiere_doi,
                     sha256_datei, vermerk_ausfall)

ADAPTER_VERSION = "0.1.0"
API = "https://api.datacite.org/dois"


def ernte(seit: str, max_seiten: int, seitengroesse: int):
    FUNDSTELLEN.mkdir(exist_ok=True)
    MANIFESTE.mkdir(parents=True, exist_ok=True)
    start = jetzt()
    lauf = f"datacite-{start.replace(':', '').replace('-', '')}"
    datei = FUNDSTELLEN / f"{lauf}.jsonl.gz"

    url = (f"{API}?resource-type-id=dataset&query=updated:%5B{seit}%20TO%20*%5D"
           f"&page%5Bcursor%5D=1&page%5Bsize%5D={seitengroesse}")
    seiten, records, vollstaendig = 0, 0, True
    gesamt_gemeldet = None

    with gzip.open(datei, "wt", encoding="utf-8") as f:
        while url and seiten < max_seiten:
            try:
                status, body, header, _ = hole(url, timeout=90)
            except RuntimeError as e:
                vermerk_ausfall("datacite", lauf, e, kontext=f"Seite {seiten + 1}")
                vollstaendig = False
                break
            if status != 200:
                vermerk_ausfall("datacite", lauf, f"HTTP {status}",
                                kontext=f"Seite {seiten + 1}: {body[:200]!r}")
                vollstaendig = False
                break
            d = json.loads(body)
            if gesamt_gemeldet is None:
                gesamt_gemeldet = (d.get("meta") or {}).get("total")
            for rec in d.get("data") or []:
                attr = rec.get("attributes") or {}
                f.write(json.dumps({
                    "quelle": "datacite",
                    "quell_id": normalisiere_doi(attr.get("doi") or rec.get("id")),
                    "geerntet": jetzt(),
                    "adapter_version": ADAPTER_VERSION,
                    "roh": attr,
                }, ensure_ascii=False) + "\n")
                records += 1
            seiten += 1
            url = (d.get("links") or {}).get("next")

    if url and seiten >= max_seiten:
        vollstaendig = False
        vermerk_ausfall("datacite", lauf, "Seitenkappe erreicht",
                        kontext=f"max_seiten={max_seiten}, weitere Seiten vorhanden")

    manifest = {
        "lauf": lauf, "quelle": "datacite", "adapter_version": ADAPTER_VERSION,
        "seit": seit, "bis": jetzt(), "seiten": seiten, "records": records,
        "gesamt_gemeldet_im_fenster": gesamt_gemeldet, "vollstaendig": vollstaendig,
        "datei": datei.name, "sha256": sha256_datei(datei),
    }
    (MANIFESTE / f"{lauf}.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return manifest


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    standard_seit = (datetime.datetime.now(datetime.timezone.utc)
                     - datetime.timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    p.add_argument("--seit", default=standard_seit,
                   help="ISO-Zeitpunkt (UTC); Standard: vor 24 h")
    p.add_argument("--max-seiten", type=int, default=60)
    p.add_argument("--seitengroesse", type=int, default=1000)
    a = p.parse_args()
    ernte(a.seit, a.max_seiten, a.seitengroesse)
