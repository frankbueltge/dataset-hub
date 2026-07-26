#!/usr/bin/env python3
"""Messung: Zenodo REST API — https://zenodo.org/api (lesend, <=7 Abfragen)."""
import datetime
import json
import urllib.parse

from mess_lib import Messung, abdeckung, histogramm

m = Messung("zenodo")
API = "https://zenodo.org/api/records"

# 1) Zähler
st, body, hdr = m.frag("zaehler", API + "?type=dataset&size=1")
if body:
    d = json.loads(body)
    m.b["zaehler"] = {"typ_dataset": d.get("hits", {}).get("total")}
    m.b["rate_limit_header"] = {k: v for k, v in (hdr or {}).items() if "ratelimit" in k}

# 2) Stichprobe: kein Zufallsparameter in der API → Convenience, ehrlich vermerkt.
# Anonyme Anfragen: max. size=25 (gemessene 400-Fehlermeldung), Rate-Limit 30/min → Drossel.
import time

recs = []
for zweck, seiten in (("stichprobe_neueste", (1, 2, 3, 4)),
                      ("stichprobe_rang4900", (197, 198, 199, 200))):
    for seite in seiten:
        st, body, hdr = m.frag(f"{zweck}_s{seite}", API + f"?type=dataset&size=25&page={seite}")
        if body and st == 200:
            d = json.loads(body)
            teil = d.get("hits", {}).get("hits", [])
            recs.extend(teil)
            if seite == seiten[0]:
                m.roh(f"zenodo-{zweck}.json.gz", body)
        time.sleep(2.5)
m.b["stichprobe"] = {
    "n": len(recs),
    "ziehung": "Convenience: 100 neueste + 100 ab Rang ~4900 (kein Zufallsparameter; anonym max. size=25) — NICHT gleichverteilt",
}


def _md(r):
    return r.get("metadata", {}) or {}


def _lizenz(r):
    md = _md(r)
    if isinstance(md.get("license"), dict) and md["license"].get("id"):
        return True
    return any((x.get("id") or x.get("title")) for x in md.get("rights") or [])


m.b["abdeckung"] = abdeckung(recs, {
    "titel": lambda r: bool((_md(r).get("title") or "").strip()),
    "urheber": lambda r: any((c.get("name") or (c.get("person_or_org") or {}).get("name") or "").strip()
                             for c in _md(r).get("creators") or []),
    "herausgeber": lambda r: bool((_md(r).get("publisher") or "").strip()),
    "zugriffs_url_landing": lambda r: bool((r.get("links") or {}).get("self_html")
                                           or (r.get("links") or {}).get("html")),
    "datei_liste": lambda r: bool(r.get("files")),
    "lizenz": _lizenz,
    "zeitraum": lambda r: bool(_md(r).get("publication_date")),
    "raeumlichkeit": lambda r: bool(_md(r).get("locations")),
    "doi": lambda r: bool(r.get("doi") or _md(r).get("doi")),
    "konzept_doi": lambda r: bool(r.get("conceptdoi") or (r.get("parent") or {}).get("id")),
})

m.b["zugangs_verteilung"] = histogramm(
    recs,
    lambda r: (r.get("access") or {}).get("files") or _md(r).get("access_right"),
)

# 3) Deep-Paging-Limit (Elasticsearch-Fenster erwartet bei 10.000)
st, body, hdr = m.frag("deep_paging_test", API + "?type=dataset&size=25&page=401")
m.b["maschinenlesbarkeit"] = {
    "format": "JSON",
    "max_size_anonym": 25,
    "deep_paging_status_rang10025": st,
}

# 4) Inkrement: OAI-PMH + updated-Query
st, body, hdr = m.frag("oai_pmh_identify", "https://zenodo.org/oai2d?verb=Identify",
                       accept="text/xml")
m.b["inkrement"] = {"oai_pmh_identify_status": st,
                    "oai_pmh_identify_ok": bool(body and b"<Identify>" in body)}

gestern = (datetime.datetime.now(datetime.timezone.utc)
           - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
q = urllib.parse.quote(f"updated:[{gestern} TO *]")
st, body, hdr = m.frag("inkrement_updated_24h", API + f"?type=dataset&size=1&q={q}")
if body and st == 200:
    d = json.loads(body)
    m.b["inkrement"]["updated_query"] = {"http_status": st,
                                         "updates_seit_gestern": d.get("hits", {}).get("total")}
else:
    m.b["inkrement"]["updated_query"] = {"http_status": st}

m.schreibe()
