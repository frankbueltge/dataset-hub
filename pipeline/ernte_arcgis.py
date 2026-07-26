#!/usr/bin/env python3
"""Ernte-Adapter ArcGIS Hub (inkrementell über filter[modified]): JSON:API,
Sparse-Fieldsets, Offset-Paginierung mit hartem 10.000er-Fenster.

Auflagen aus der Messung (messungen/ergebnisse/2026-07-26-arcgis.md), bindend:

(1) Sparse-Fieldsets (`fields[datasets]=...`) sind ZWINGEND — der Default-Payload
    ist bis zu 50× größer (komplettes Feature-Service-Schema pro Record), ohne
    zusätzliche Abdeckung für die hier genutzten Felder.
(2) `sort=-modified` ist Datenmüll (mindestens ein Record trägt einen Zeitstempel
    im Jahr ~3000) und wird darum NICHT verwendet. Inkrement ausschließlich über
    `filter[modified]=YYYY/MM/DD` — dieser Filter wirkt KUMULATIV ("seit diesem
    Datum bis jetzt"), nicht als Tagesfenster.
(3) Hartes Fenster bei Offset+Size = 10.000 (HTTP 500, explizite Fehlermeldung
    "Result window is too large", kein Cursor, keine Scroll-API zugänglich
    gemacht). Wird erkannt und im Manifest als Unvollständigkeit vermerkt —
    niemals als stilles "fertig" missverstanden.
(4) Dedup NICHT hier: der Zähler zählt (Item × Layer)-Kombinationen, nur ~51,5 %
    eindeutige `itemId` in der Stichprobe (ein Service tauchte 45× auf). quell_id
    ist deshalb bewusst `itemId`, nicht der Layer-spezifische `id` — Begründung
    und Auswirkung stehen bei `normalisiere_arcgis` in normalisiere.py.

Schreibt Fundstellen wörtlich (roh = volles JSON:API-Resource-Objekt, unverändert)
als JSONL.gz plus Manifest mit Zähler, SHA-256 und Vollständigkeits-Flag.
"""
import argparse
import datetime
import gzip
import json

from hub_lib import FUNDSTELLEN, MANIFESTE, hole, jetzt, sha256_datei, vermerk_ausfall

ADAPTER_VERSION = "0.1.0"
API = "https://hub.arcgis.com/api/v3/datasets"
FELDER = ("name,owner,orgName,organization,source,url,type,modified,"
          "license,structuredLicense,extent,itemId")
SEITENGROESSE = 100
HARTES_FENSTER = 10000


def ernte(seit: str, max_seiten: int, seitengroesse: int):
    FUNDSTELLEN.mkdir(exist_ok=True)
    MANIFESTE.mkdir(parents=True, exist_ok=True)
    start = jetzt()
    lauf = f"arcgis-{start.replace(':', '').replace('-', '')}"
    datei = FUNDSTELLEN / f"{lauf}.jsonl.gz"

    url = (f"{API}?page[size]={seitengroesse}&fields[datasets]={FELDER}"
           f"&filter[modified]={seit}")
    seiten, records, vollstaendig = 0, 0, True
    gesamt_gemeldet = None
    hinweis = None

    with gzip.open(datei, "wt", encoding="utf-8") as f:
        while url and seiten < max_seiten:
            try:
                status, body, header, _ = hole(url, timeout=90)
            except RuntimeError as e:
                vermerk_ausfall("arcgis", lauf, e, kontext=f"Seite {seiten + 1}")
                vollstaendig = False
                hinweis = f"Netzausfall bei Seite {seiten + 1}"
                break
            if status == 500 and b"Result window is too large" in body:
                # Auflage 3: das harte 10k-Fenster meldet sich explizit per HTTP
                # 500 — kein stilles Leerlaufen, aber trotzdem kein "fertig".
                vollstaendig = False
                hinweis = f"10k-Fenster (HTTP 500) bei Seite {seiten + 1}"
                vermerk_ausfall("arcgis", lauf,
                                "HTTP 500: Result window is too large (10k-Fenster)",
                                kontext=f"Seite {seiten + 1}")
                break
            if status != 200:
                vermerk_ausfall("arcgis", lauf, f"HTTP {status}",
                                kontext=f"Seite {seiten + 1}: {body[:200]!r}")
                vollstaendig = False
                hinweis = f"HTTP {status} bei Seite {seiten + 1}"
                break
            d = json.loads(body)
            if gesamt_gemeldet is None:
                meta = d.get("meta") or {}
                gesamt_gemeldet = meta.get("total") or (meta.get("stats") or {}).get("totalCount")
            daten = d.get("data") or []
            if not daten:
                # Echtes Ende des filter[modified]-Fensters — das 10k-Fenster
                # meldet sich per HTTP 500 (siehe oben), nicht per leerem Array.
                break
            for rec in daten:
                attr = rec.get("attributes") or {}
                quell_id = attr.get("itemId") or rec.get("id") or ""
                f.write(json.dumps({
                    "quelle": "arcgis",
                    "quell_id": quell_id,
                    "geerntet": jetzt(),
                    "adapter_version": ADAPTER_VERSION,
                    "roh": rec,
                }, ensure_ascii=False) + "\n")
                records += 1
            seiten += 1
            url = (d.get("links") or {}).get("next")

    if vollstaendig and url and seiten >= max_seiten:
        vollstaendig = False
        hinweis = "Seitenkappe erreicht, weitere Seiten möglich"
        vermerk_ausfall("arcgis", lauf, "Seitenkappe erreicht",
                        kontext=f"max_seiten={max_seiten}")

    manifest = {
        "lauf": lauf, "quelle": "arcgis", "adapter_version": ADAPTER_VERSION,
        "seit_modified": seit, "bis": jetzt(), "seiten": seiten, "records": records,
        "seitengroesse": seitengroesse,
        "gesamt_gemeldet_im_fenster": gesamt_gemeldet, "vollstaendig": vollstaendig,
        "hinweis": hinweis,
        "datei": datei.name, "sha256": sha256_datei(datei),
    }
    (MANIFESTE / f"{lauf}.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return manifest


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    gestern = (datetime.datetime.now(datetime.timezone.utc)
               - datetime.timedelta(days=1)).strftime("%Y/%m/%d")
    p.add_argument("--seit", default=gestern,
                   help="Datum YYYY/MM/DD für filter[modified] (kumulativ, "
                        "'seit diesem Datum bis jetzt'); Standard: gestern")
    p.add_argument("--max-seiten", type=int, default=3)
    p.add_argument("--seitengroesse", type=int, default=SEITENGROESSE)
    a = p.parse_args()
    ernte(a.seit, a.max_seiten, a.seitengroesse)
