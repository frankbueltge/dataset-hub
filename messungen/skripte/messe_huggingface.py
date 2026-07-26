#!/usr/bin/env python3
"""Messung: HuggingFace Hub API — /api/datasets (lesend; Zähl-Iteration mit Kappe)."""
import json
import re
import time

from mess_lib import Messung, abdeckung, hole

m = Messung("huggingface")
API = "https://huggingface.co/api/datasets"

# 1) Header-Befund: liefert die API einen Zähler?
st, body, hdr = m.frag("header_check", API + "?limit=1")
m.b["header_befund"] = {
    "x_total_count": (hdr or {}).get("x-total-count"),
    "link_header_vorhanden": bool((hdr or {}).get("link")),
}

# 2) Zähl-Iteration über den Link-Header (Cursor), Kappe als ehrliche Grenze
KAPPE = 120
SEITENGROESSE = 1000
gezaehlt, seiten = 0, 0
url = API + f"?limit={SEITENGROESSE}"
naechste = re.compile(r'<([^>]+)>;\s*rel="next"')
m.b["abfragen"].append({"zweck": "zaehl_iteration",
                        "url": url,
                        "hinweis": f"Folge-Cursor via Link-Header, Kappe {KAPPE} Seiten à {SEITENGROESSE}"})
try:
    while url and seiten < KAPPE:
        st, body, hdr = hole(url, timeout=60)
        if st != 200:
            m.b["ausfaelle"].append({"zweck": "zaehl_iteration", "url": url, "http_status": st})
            break
        d = json.loads(body)
        gezaehlt += len(d)
        seiten += 1
        treffer = naechste.search((hdr or {}).get("link") or "")
        url = treffer.group(1) if treffer else None
        time.sleep(0.25)
except RuntimeError as e:
    m.b["ausfaelle"].append({"zweck": "zaehl_iteration", "fehler": str(e)})
m.b["zaehler"] = {
    "iteriert": gezaehlt,
    "seiten": seiten,
    "vollstaendig": url is None and seiten < KAPPE,
}
if url is not None:
    m.b["zaehler"]["hinweis"] = (f"Iteration bei Kappe ({KAPPE} Seiten) gestoppt — "
                                 f"tatsächlicher Bestand GRÖSSER als {gezaehlt}")

# 3) Stichprobe mit vollen Metadaten (Standardsortierung → Convenience)
st, body, hdr = m.frag("stichprobe", API + "?limit=200&full=true")
recs = []
if body and st == 200:
    recs = json.loads(body)
    m.roh("huggingface-stichprobe.json.gz", body)
m.b["stichprobe"] = {
    "n": len(recs),
    "ziehung": "Convenience: erste 200 der Standardsortierung, full=true — NICHT gleichverteilt",
}


def _lizenz(r):
    tags = r.get("tags") or []
    if any(isinstance(t, str) and t.startswith("license:") for t in tags):
        return True
    return bool((r.get("cardData") or {}).get("license"))


m.b["abdeckung"] = abdeckung(recs, {
    "id": lambda r: bool(r.get("id")),
    "autor_im_namensraum": lambda r: "/" in (r.get("id") or ""),
    "lizenz": _lizenz,
    "beschreibung": lambda r: bool((r.get("description") or "").strip()
                                   or (r.get("cardData") or {}).get("dataset_summary")),
    "lastModified": lambda r: bool(r.get("lastModified")),
    "createdAt": lambda r: bool(r.get("createdAt")),
    "explizites_url_feld": lambda r: bool(r.get("url") or r.get("html_url")),
    "downloads_zaehler": lambda r: r.get("downloads") is not None,
})

# 4) Inkrement: Sortierung nach lastModified
st, body, hdr = m.frag("inkrement_sort_lastModified",
                       API + "?limit=1&sort=lastModified&direction=-1")
eintrag = {"http_status": st}
if body and st == 200:
    d = json.loads(body)
    if d:
        eintrag["neuestes_lastModified"] = d[0].get("lastModified")
m.b["inkrement"] = eintrag

m.schreibe()
