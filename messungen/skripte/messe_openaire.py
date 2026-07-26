#!/usr/bin/env python3
"""Messung: OpenAIRE (Graph-API-Test + Legacy-Search-API; lesend, <=10 Abfragen)."""
import json

from mess_lib import Messung, abdeckung, histogramm

m = Messung("openaire")


def L(x):
    """Die Legacy-JSON-Antwort liefert je nach Kardinalität Objekt ODER Liste."""
    return x if isinstance(x, list) else ([] if x is None else [x])


def T(x):
    """Textwerte stecken in {'$': …}."""
    if isinstance(x, dict):
        return x.get("$")
    return x


# 1) Graph-API anonym erreichbar? (zwei bekannte Pfadvarianten)
m.b["graph_api"] = []
for url in ("https://api.openaire.eu/graph/v1/researchProducts?type=dataset&pageSize=1",
            "https://api.openaire.eu/graph/researchProducts?type=dataset&pageSize=1"):
    st, body, hdr = m.frag("graph_api_test", url)
    eintrag = {"url": url, "http_status": st}
    if body and st == 200:
        try:
            d = json.loads(body)
            eintrag["numFound"] = (d.get("header") or {}).get("numFound")
        except Exception:
            eintrag["antwort_kein_json"] = True
    m.b["graph_api"].append(eintrag)

# 2) Legacy-Zähler
API = "https://api.openaire.eu/search/datasets"
st, body, hdr = m.frag("zaehler", API + "?format=json&size=1")
if body and st == 200:
    d = json.loads(body)
    m.b["zaehler"] = {"datasets": T((d.get("response") or {}).get("header", {}).get("total"))}
    m.b["rate_limit_header"] = {k: v for k, v in (hdr or {}).items()
                                if "ratelimit" in k or "rate-limit" in k}

# 3) Stichprobe: 4 Seiten à 50 (kein Zufallsparameter → Convenience)
recs = []
for seite in (1, 2, 3, 4):
    st, body, hdr = m.frag(f"stichprobe_seite{seite}", API + f"?format=json&size=50&page={seite}")
    if body and st == 200:
        d = json.loads(body)
        teil = L(((d.get("response") or {}).get("results") or {}).get("result"))
        recs.extend(teil)
        if seite == 1:
            m.roh("openaire-stichprobe-seite1.json.gz", body)
m.b["stichprobe"] = {
    "n": len(recs),
    "ziehung": "Convenience: Seiten 1–4 der Standardsortierung — NICHT gleichverteilt",
}


def _md(r):
    return ((r.get("metadata") or {}).get("oaf:entity") or {}).get("oaf:result") or {}


def _instanzen(r):
    return L((_md(r).get("children") or {}).get("instance"))


def _urls(r):
    aus = []
    for inst in _instanzen(r):
        for w in L(inst.get("webresource")):
            u = T(w.get("url")) if isinstance(w, dict) else None
            if u:
                aus.append(u)
    return aus


m.b["abdeckung"] = abdeckung(recs, {
    "titel": lambda r: any((T(t) or "").strip() for t in L(_md(r).get("title"))),
    "urheber": lambda r: any((T(c) or "").strip() for c in L(_md(r).get("creator"))),
    "herausgeber": lambda r: bool((T(_md(r).get("publisher")) or "").strip()),
    "zugriffs_url": lambda r: bool(_urls(r)),
    "lizenz_an_instanz": lambda r: any(T(i.get("license")) for i in _instanzen(r)),
    "zeitraum": lambda r: bool(T(_md(r).get("dateofacceptance"))),
    "pid_doi": lambda r: any(isinstance(p, dict) and p.get("@classid") == "doi"
                             for p in L(_md(r).get("pid"))),
})

m.b["zugangsrecht_verteilung"] = histogramm(
    recs, lambda r: (_md(r).get("bestaccessright") or {}).get("@classname"),
)

# 4) Deep-Paging-Test (Fenstergrenze der Legacy-API)
st, body, hdr = m.frag("deep_paging_test", API + "?format=json&size=50&page=250")
m.b["maschinenlesbarkeit"] = {"format": "JSON (verschachteltes oaf-Schema)",
                              "deep_paging_status_seite250x50": st}

m.schreibe()
