#!/usr/bin/env python3
"""Überlappungsmessung: Wie viele DOIs der DataCite-Zufallsstichprobe kennt OpenAIRE?

Eingabe ist die committete Rohdatei der DataCite-Messung — dieselben DOIs, keine
neue Ziehung. Gedrosselt (1,2 s), damit die anonyme Legacy-API nicht strapaziert wird.
"""
import gzip
import json
import time
import urllib.parse

from mess_lib import Messung, ROHDATEN, hole

m = Messung("ueberlappung-datacite-openaire")

QUELLE = ROHDATEN / "datacite-stichprobe.json.gz"
d = json.loads(gzip.decompress(QUELLE.read_bytes()))
dois = [(r.get("attributes") or {}).get("doi") for r in d.get("data", [])]
dois = [x for x in dois if x]
m.b["eingabe"] = {"rohdatei": "rohdaten/datacite-stichprobe.json.gz", "dois": len(dois)}
m.b["abfragen"].append({
    "zweck": "doi_lookup_je_eintrag",
    "url_muster": "https://api.openaire.eu/search/datasets?format=json&doi=<doi>&size=1",
    "drossel_s": 1.2,
})

gefunden, http_fehler = 0, 0
einzel = []
for doi in dois:
    url = ("https://api.openaire.eu/search/datasets?format=json&size=1&doi="
           + urllib.parse.quote(doi, safe=""))
    try:
        st, body, hdr = hole(url, timeout=40)
        if st == 200:
            total = ((json.loads(body).get("response") or {}).get("header") or {}).get("total")
            if isinstance(total, dict):
                total = total.get("$")
            treffer = int(total or 0)
            gefunden += 1 if treffer > 0 else 0
            einzel.append({"doi": doi, "openaire_treffer": treffer})
        else:
            http_fehler += 1
            einzel.append({"doi": doi, "http_status": st})
    except RuntimeError as e:
        m.b["ausfaelle"].append({"doi": doi, "fehler": str(e)})
        einzel.append({"doi": doi, "ausfall": True})
    time.sleep(1.2)

geprueft = len([e for e in einzel if "openaire_treffer" in e])
m.b["ergebnis"] = {
    "dois_gesamt": len(dois),
    "erfolgreich_geprueft": geprueft,
    "in_openaire_gefunden": gefunden,
    "http_fehler": http_fehler,
    "ausfaelle": len(m.b["ausfaelle"]),
    "anteil_gefunden": round(gefunden / geprueft, 3) if geprueft else None,
}
m.b["einzel"] = einzel

m.schreibe()
