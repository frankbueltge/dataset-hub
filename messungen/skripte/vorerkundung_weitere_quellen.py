#!/usr/bin/env python3
"""Vorerkundung weiterer Quellkandidaten (Stichproben-Zähler, keine volle Messung).

Kandidaten: Socrata Discovery (US/EU), OpenDataSoft-Netzwerk, Dataverse (Harvard),
OpenML, Kaggle (unauthentifiziert), ArcGIS Hub, data.gov-DCAT-Export sowie zwei
kuratierte GitHub-Listen (awesome-public-datasets, curran/data) inkl. einer kleinen
Link-Rot-Stichprobe. Jede Zahl stammt aus einer gespeicherten Antwort.
"""
import json
import re
import time
import urllib.error
import urllib.request

from mess_lib import UA, Messung, hole

m = Messung("vorerkundung-weitere-quellen")

# ---- API-Kataloge: nur Zähler-Stichproben --------------------------------------
PROBEN = [
    ("socrata_discovery_us", "https://api.us.socrata.com/api/catalog/v1?only=datasets&limit=1",
     lambda d: {"resultSetSize": d.get("resultSetSize")}),
    ("socrata_discovery_eu", "https://api.eu.socrata.com/api/catalog/v1?only=datasets&limit=1",
     lambda d: {"resultSetSize": d.get("resultSetSize")}),
    ("opendatasoft_netzwerk", "https://data.opendatasoft.com/api/explore/v2.1/catalog/datasets?limit=1",
     lambda d: {"total_count": d.get("total_count")}),
    ("dataverse_harvard", "https://dataverse.harvard.edu/api/search?q=*&type=dataset&per_page=1",
     lambda d: {"total_count": (d.get("data") or {}).get("total_count")}),
    ("openml", "https://www.openml.org/api/v1/json/data/list/limit/1",
     lambda d: {"antwort_schluessel": sorted(d.keys()),
                "hinweis": "kein Gesamtzähler in dieser Antwort erkennbar"
                if "count" not in json.dumps(d)[:200] else None}),
    ("kaggle_unauthentifiziert", "https://www.kaggle.com/api/v1/datasets/list?page=1",
     lambda d: {"n_in_antwort": len(d) if isinstance(d, list) else None,
                "hat_url_feld": bool(isinstance(d, list) and d and d[0].get("url")),
                "hat_lizenz_feld": bool(isinstance(d, list) and d and d[0].get("licenseName")),
                "hat_urheber_feld": bool(isinstance(d, list) and d and d[0].get("creatorName"))}),
    ("arcgis_hub", "https://hub.arcgis.com/api/v3/datasets?page%5Bsize%5D=1",
     lambda d: {"meta_schluessel": sorted((d.get("meta") or {}).keys()),
                "stats": (d.get("meta") or {}).get("stats"),
                "total": (d.get("meta") or {}).get("total"),
                "daten_anzahl_in_antwort": len(d.get("data") or [])}),
]

m.b["proben"] = []
for name, url, extrakt in PROBEN:
    st, body, hdr = m.frag(name, url, timeout=45)
    eintrag = {"name": name, "url": url, "http_status": st}
    if body is not None and st == 200:
        try:
            d = json.loads(body)
            eintrag["befund"] = {k: v for k, v in (extrakt(d) or {}).items() if v is not None}
            m.roh(f"vorerkundung-{name}.json.gz", body)
        except Exception as e:
            eintrag["antwort_kein_json"] = str(e)[:120]
            eintrag["antwort_anfang"] = body[:150].decode("utf-8", errors="replace")
    elif body is not None:
        eintrag["antwort_anfang"] = body[:150].decode("utf-8", errors="replace")
    m.b["proben"].append(eintrag)
    time.sleep(0.5)

# ---- data.gov: DCAT-US-Export vorhanden? (nur HEAD, Datei kann riesig sein) ----
try:
    req = urllib.request.Request("https://catalog.data.gov/data.json", method="HEAD",
                                 headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        m.b["datagov_data_json"] = {"http_status": r.status,
                                    "content_type": r.headers.get("Content-Type"),
                                    "content_length": r.headers.get("Content-Length")}
except urllib.error.HTTPError as e:
    m.b["datagov_data_json"] = {"http_status": e.code}
except Exception as e:
    m.b["ausfaelle"].append({"zweck": "datagov_data_json_head", "fehler": str(e)})

# ---- Kuratierte GitHub-Listen ---------------------------------------------------
LISTEN = [
    ("awesome_public_datasets", "https://api.github.com/repos/awesomedata/awesome-public-datasets"),
    ("curran_data", "https://api.github.com/repos/curran/data"),
]
m.b["listen"] = []
link_muster = re.compile(r"https?://[^\s\)\]\"'<>]+")
awesome_links = []
for name, repo_url in LISTEN:
    eintrag = {"name": name}
    st, body, hdr = m.frag(f"{name}_repo", repo_url)
    if body and st == 200:
        d = json.loads(body)
        eintrag["letzter_push"] = d.get("pushed_at")
        eintrag["stars"] = d.get("stargazers_count")
    st, body, hdr = m.frag(f"{name}_readme", repo_url + "/readme",
                           accept="application/vnd.github.raw")
    if body and st == 200:
        text = body.decode("utf-8", errors="replace")
        m.roh(f"vorerkundung-{name}-readme.md.gz", body)
        links = [l for l in link_muster.findall(text)
                 if "github.com/awesomedata" not in l and "shields.io" not in l
                 and "githubusercontent" not in l]
        eintrag["links_im_readme"] = len(links)
        eintrag["eindeutige_domains"] = len({re.sub(r"^https?://([^/]+).*", r"\1", l) for l in links})
        if name == "awesome_public_datasets":
            awesome_links = links
    m.b["listen"].append(eintrag)

# ---- Link-Rot-Stichprobe: jeder k-te Link der awesome-Liste, n=20 ---------------
if awesome_links:
    k = max(1, len(awesome_links) // 20)
    probe = awesome_links[::k][:20]
    stati = {}
    einzel = []
    for url in probe:
        try:
            st, body, hdr = hole(url, timeout=15, versuche=1, accept="*/*")
            klasse = f"{st // 100}xx"
        except RuntimeError:
            klasse = "ausfall"
            st = None
        stati[klasse] = stati.get(klasse, 0) + 1
        einzel.append({"url": url[:120], "status": st})
        time.sleep(0.3)
    m.b["link_rot_stichprobe"] = {
        "n": len(probe),
        "ziehung": f"jeder {k}. Link des README, deterministisch",
        "status_klassen": stati,
        "einzel": einzel,
    }

m.schreibe()
