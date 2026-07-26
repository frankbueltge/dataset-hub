#!/usr/bin/env python3
"""Messung: DataCite REST API — https://api.datacite.org (lesend, <=5 Abfragen)."""
import datetime
import json

from mess_lib import Messung, abdeckung

m = Messung("datacite")
API = "https://api.datacite.org/dois"

# 1) Zähler + Facetten (Lizenzverteilung über den Gesamtbestand liefert die API mit)
st, body, hdr = m.frag("zaehler", API + "?resource-type-id=dataset&page%5Bsize%5D=1")
if body:
    d = json.loads(body)
    meta = d.get("meta", {})
    m.b["zaehler"] = {"typ_dataset": meta.get("total")}
    m.b["facetten"] = {k: meta.get(k) for k in ("licenses", "states", "published") if meta.get(k)}
    m.b["rate_limit_header"] = {k: v for k, v in (hdr or {}).items() if "ratelimit" in k}

# 2) Stichprobe, API-seitig zufällig (random=true)
st, body, hdr = m.frag("stichprobe", API + "?resource-type-id=dataset&random=true&page%5Bsize%5D=200")
recs = []
if body:
    d = json.loads(body)
    recs = [r.get("attributes", {}) for r in d.get("data", [])]
    m.b["rohdatei"] = m.roh("datacite-stichprobe.json.gz", body)
    m.b["stichprobe"] = {"n": len(recs), "ziehung": "random=true (API-seitig zufällig)"}


def _publisher(r):
    p = r.get("publisher")
    if isinstance(p, dict):
        return bool((p.get("name") or "").strip())
    return bool((p or "").strip())


m.b["abdeckung"] = abdeckung(recs, {
    "titel": lambda r: any((t.get("title") or "").strip() for t in r.get("titles") or []),
    "urheber": lambda r: any((c.get("name") or c.get("familyName") or "").strip()
                             for c in r.get("creators") or []),
    "herausgeber": _publisher,
    "zugriffs_url": lambda r: bool((r.get("url") or "").strip()),
    "lizenz": lambda r: any(x.get("rightsIdentifier") or x.get("rightsUri") or x.get("rights")
                            for x in r.get("rightsList") or []),
    "zeitraum": lambda r: bool(r.get("publicationYear")) or any(x.get("date") for x in r.get("dates") or []),
    "raeumlichkeit": lambda r: bool(r.get("geoLocations")),
    "format_oder_groesse": lambda r: bool(r.get("formats")) or bool(r.get("sizes")),
})

# 3) Volliterierbarkeit: Cursor-Paginierung
st, body, hdr = m.frag("cursor_test", API + "?resource-type-id=dataset&page%5Bcursor%5D=1&page%5Bsize%5D=1")
if body:
    d = json.loads(body)
    m.b["maschinenlesbarkeit"] = {
        "format": "JSON:API",
        "cursor_paginierung": bool(d.get("links", {}).get("next")),
    }

# 4) Inkrement: updated-Abfrage der letzten 24 h (Tagesvolumen)
gestern = (datetime.datetime.now(datetime.timezone.utc)
           - datetime.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
url = API + f"?resource-type-id=dataset&query=updated:%5B{gestern}%20TO%20*%5D&page%5Bsize%5D=1"
st, body, hdr = m.frag("inkrement_updated_24h", url)
if body:
    d = json.loads(body)
    m.b["inkrement"] = {
        "weg": "query=updated:[T-24h TO *]",
        "http_status": st,
        "updates_24h_typ_dataset": d.get("meta", {}).get("total"),
    }

m.schreibe()
