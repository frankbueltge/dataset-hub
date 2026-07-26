#!/usr/bin/env python3
"""Messung: EU Open Data Portal (data.europa.eu, hub-search API; lesend, <=7 Abfragen)."""
import json

from mess_lib import Messung, abdeckung, histogramm

m = Messung("eudp")
API = "https://data.europa.eu/api/hub/search/search"

# 1) Zähler gesamt und mit Dataset-Filter
st, body, hdr = m.frag("zaehler_gesamt", API + "?limit=1")
if body:
    d = json.loads(body)
    m.b["zaehler"] = {"gesamt": (d.get("result") or {}).get("count")}
st, body, hdr = m.frag("zaehler_dataset", API + "?filter=dataset&limit=1")
if body:
    d = json.loads(body)
    m.b.setdefault("zaehler", {})["filter_dataset"] = (d.get("result") or {}).get("count")

# 2) Stichprobe: zwei Seiten (kein Zufallsparameter bekannt → Convenience)
recs = []
for zweck, seite in (("stichprobe_seite0", 0), ("stichprobe_seite50", 50)):
    st, body, hdr = m.frag(zweck, API + f"?filter=dataset&limit=100&page={seite}")
    if body and st == 200:
        d = json.loads(body)
        teil = (d.get("result") or {}).get("results") or []
        recs.extend(teil)
        m.roh(f"eudp-{zweck}.json.gz", body)
m.b["stichprobe"] = {
    "n": len(recs),
    "ziehung": "Convenience: Seite 0 und Seite 50 der Standardsortierung — NICHT gleichverteilt",
}


def _sprachwert(x):
    """Mehrsprachige Felder sind Dicts {'de': …, 'en': …}."""
    if isinstance(x, dict):
        return any((v or "").strip() for v in x.values() if isinstance(v, str))
    if isinstance(x, str):
        return bool(x.strip())
    return bool(x)


def _distributionen(r):
    return r.get("distributions") or []


m.b["abdeckung"] = abdeckung(recs, {
    "titel": lambda r: _sprachwert(r.get("title")),
    "urheber": lambda r: bool(r.get("creator")),
    "herausgeber": lambda r: bool(((r.get("publisher") or {}).get("name") or "").strip()
                                  if isinstance(r.get("publisher"), dict) else r.get("publisher")),
    "zugriffs_url": lambda r: any((dist.get("access_url") or dist.get("download_url"))
                                  for dist in _distributionen(r)),
    "lizenz": lambda r: any((dist.get("licence") or dist.get("license"))
                            for dist in _distributionen(r)) or bool(r.get("licence")),
    "zeitraum": lambda r: bool(r.get("temporal")),
    "raeumlichkeit": lambda r: bool(r.get("spatial")),
    "format": lambda r: any(dist.get("format") for dist in _distributionen(r)),
    "modified": lambda r: bool(r.get("modified")),
})

m.b["katalog_verteilung"] = histogramm(
    recs, lambda r: ((r.get("catalog") or {}).get("id")), maxi=12,
)

# 3) Deep-Paging-Test
st, body, hdr = m.frag("deep_paging_test", API + "?filter=dataset&limit=100&page=5000")
m.b["maschinenlesbarkeit"] = {"format": "JSON", "deep_paging_status_seite5000x100": st}

# 4) Inkrement: Sortierung nach modified
st, body, hdr = m.frag("sort_modified_test", API + "?filter=dataset&limit=1&sort=modified%2Bdesc")
eintrag = {"sort_modified_status": st}
if body and st == 200:
    d = json.loads(body)
    ergebnisse = (d.get("result") or {}).get("results") or []
    if ergebnisse:
        eintrag["neuestes_modified"] = ergebnisse[0].get("modified")
m.b["inkrement"] = eintrag

m.schreibe()
