#!/usr/bin/env python3
"""Klärung: data.gov — die Standard-CKAN-API antwortete am 2026-07-26 mit HTTP 404.

Prüft dokumentierte Pfadvarianten und Nachbar-Endpunkte, protokolliert Status,
Content-Type und Antwortanfang. Erfindet keine Erklärung: was hier steht, wurde
tatsächlich abgerufen.
"""
import re

from mess_lib import Messung

m = Messung("datagov-klaerung")

VARIANTEN = [
    ("ckan_v3_package_search", "https://catalog.data.gov/api/3/action/package_search?rows=1"),
    ("ckan_ohne_version", "https://catalog.data.gov/api/action/package_search?rows=1"),
    ("ckan_site_read", "https://catalog.data.gov/api/3/action/site_read"),
    ("api_wurzel", "https://catalog.data.gov/api/3"),
    ("katalog_html", "https://catalog.data.gov/dataset"),
    ("www_startseite", "https://www.data.gov/"),
    ("entwickler_seite", "https://data.gov/developers/"),
    ("api_data_gov", "https://api.data.gov/"),
]

m.b["befunde"] = []
for name, url in VARIANTEN:
    st, body, hdr = m.frag(name, url, accept="*/*", timeout=30)
    befund = {"name": name, "url": url, "http_status": st}
    if body is not None:
        befund["content_type"] = (hdr or {}).get("content-type")
        text = body[:1500].decode("utf-8", errors="replace")
        titel = re.search(r"<title[^>]*>(.*?)</title>", text, re.S | re.I)
        if titel:
            befund["html_titel"] = titel.group(1).strip()[:200]
        else:
            befund["antwort_anfang"] = text[:200]
    m.b["befunde"].append(befund)

m.schreibe()
