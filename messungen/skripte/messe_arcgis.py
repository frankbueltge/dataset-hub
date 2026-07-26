#!/usr/bin/env python3
"""Messung: ArcGIS Hub API — https://hub.arcgis.com/api/v3/datasets (lesend, ~11 Abfragen).

Vorerkundung: meta.total = 21.104.755 (`2026-07-26-vorerkundung-weitere-quellen.md`).
Offene Frage dort: was zählt als „dataset"? Diese Messung klärt das über die
Typenverteilung UND über den Anteil eindeutiger `itemId` in der Stichprobe (Verdacht:
ein AGOL-Item mit mehreren Layern erzeugt mehrere „dataset"-Records).
"""
import collections
import datetime
import json
import time

from mess_lib import Messung, abdeckung, histogramm

m = Messung("arcgis")
API = "https://hub.arcgis.com/api/v3/datasets"
PAUSE = 0.3

# 1) Zähler (zweimal im Lauf abgefragt, um Live-Schwankung direkt zu belegen) -------
st, body, hdr = m.frag("zaehler", API + "?page%5Bsize%5D=1")
if body and st == 200:
    d = json.loads(body)
    m.b["zaehler"] = {
        "total_meta_total": (d.get("meta") or {}).get("total"),
        "total_stats_totalCount": ((d.get("meta") or {}).get("stats") or {}).get("totalCount"),
        "last_link": (d.get("links") or {}).get("last"),
    }
    m.b["rate_limit_header"] = {k: v for k, v in (hdr or {}).items() if "ratelimit" in k}
time.sleep(PAUSE)

# 2) Stichprobe über zwei getrennte Seiten kombiniert (n>=200, "mehrere Seiten") ----
recs = []
seite1_bytes = None
for zweck, seite in (("stichprobe_seite1", 1), ("stichprobe_seite51", 51)):
    url = API + f"?page%5Bsize%5D=100&page%5Bnumber%5D={seite}"
    st, body, hdr = m.frag(zweck, url)
    if body and st == 200:
        d = json.loads(body)
        for item in d.get("data") or []:
            a = dict(item.get("attributes") or {})
            a["_id"] = item.get("id")
            a["_itemPage"] = (item.get("links") or {}).get("itemPage")
            recs.append(a)
        m.roh(f"arcgis-{zweck}.json.gz", body)
        if seite == 1:
            seite1_bytes = len(body)
    time.sleep(PAUSE)
m.b["stichprobe"] = {
    "n": len(recs),
    "ziehung": "Convenience: Seite 1 und Seite 51 (je size=100) der Standardsortierung "
               "(kein Zufallsparameter bekannt) — NICHT gleichverteilt",
}


def _herausgeber(r):
    return bool((r.get("orgName") or r.get("organization") or r.get("source") or "").strip())


def _hat_temporalschluessel(x, tiefe=0):
    """Rekursive Suche nach FGDC/ISO-Temporalfeldern im optionalen metadata-Blob."""
    if tiefe > 6:
        return False
    if isinstance(x, dict):
        for k, v in x.items():
            if k in ("tempKw", "TempExtent", "tempExtent", "srchDates", "dataExt"):
                return True
            if _hat_temporalschluessel(v, tiefe + 1):
                return True
        return False
    if isinstance(x, list):
        return any(_hat_temporalschluessel(v, tiefe + 1) for v in x)
    return False


m.b["abdeckung"] = abdeckung(recs, {
    "titel": lambda r: bool((r.get("name") or "").strip()),
    "urheber": lambda r: bool((r.get("owner") or "").strip()),
    "herausgeber": _herausgeber,
    "zugriffs_url": lambda r: bool((r.get("url") or "").strip()),
    "landingpage_url": lambda r: bool((r.get("_itemPage") or "").strip()),
    "lizenz": lambda r: bool((r.get("license") or "").strip()) or bool(r.get("structuredLicense")),
    "zeitraum_metadata_temporalfeld": lambda r: _hat_temporalschluessel(r.get("metadata")),
    "raeumlichkeit": lambda r: bool(r.get("extent")) or bool(r.get("itemExtent")),
    "format_typ": lambda r: bool((r.get("type") or "").strip()),
    "aenderungsdatum": lambda r: bool(r.get("modified")),
})

# 3) Was zählt als "dataset"? Typenverteilung + Anteil eindeutiger itemId -----------
n = len(recs)
itemids = [r.get("itemId") for r in recs if r.get("itemId")]
zaehlung = collections.Counter(itemids)
mehrfach = {k: v for k, v in zaehlung.items() if v > 1}
m.b["was_zaehlt_als_dataset"] = {
    "erlaeuterung": "Jeder Record ist ein AGOL-Item ODER ein einzelner Layer/eine Tabelle "
                    "innerhalb eines Multi-Layer-Feature-Service — der `id`-Suffix (_0, _1, "
                    "_22, ...) ist der Layer-Index. `itemId` identifiziert das zugrundeliegende "
                    "AGOL-Item; wiederholte itemId = mehrere Layer desselben Service, je als "
                    "eigener \"dataset\"-Record gezählt.",
    "typ_verteilung": histogramm(recs, lambda r: r.get("type")),
    "hubType_verteilung": histogramm(recs, lambda r: r.get("hubType")),
    "eindeutige_itemId": {
        "n_records": n,
        "n_eindeutige_itemId": len(zaehlung),
        "anteil_eindeutig": round(len(zaehlung) / n, 3) if n else None,
        "records_mit_mehrfach_gezaehlter_itemId": sum(mehrfach.values()),
    },
    "beispiel_mehrfachzaehlung_top5": dict(sorted(mehrfach.items(), key=lambda kv: -kv[1])[:5]),
    "herkunft_sector_verteilung": histogramm(recs, lambda r: r.get("sector")),
    "herkunft_region_verteilung": histogramm(recs, lambda r: r.get("region")),
    "openData_flag_verteilung": histogramm(recs, lambda r: r.get("openData")),
    "access_verteilung": histogramm(recs, lambda r: r.get("access")),
}
time.sleep(PAUSE)

# 4) Volliterierbarkeit: Deep-Paging-Grenze exakt bestimmen ------------------------
st_ok, body_ok, _ = m.frag("deep_paging_grenze_10000",
                           API + "?page%5Bsize%5D=1&page%5Bnumber%5D=10000")
time.sleep(PAUSE)
st_fail, body_fail, _ = m.frag("deep_paging_grenze_10001",
                               API + "?page%5Bsize%5D=1&page%5Bnumber%5D=10001")
time.sleep(PAUSE)
st_cursor, body_cursor, _ = m.frag("cursor_test_ablehnung",
                                   API + "?page%5Bcursor%5D=1&page%5Bsize%5D=1")
time.sleep(PAUSE)
fehlermeldung_10001 = None
if body_fail:
    try:
        fehlermeldung_10001 = json.loads(body_fail).get("errors", [{}])[0].get("message")
    except Exception:
        pass
m.b["maschinenlesbarkeit"] = {
    "format": "JSON:API",
    "paginierung": "page[number]/page[size] (Offset) — page[cursor] wird abgelehnt (400, "
                   "\"'cursor' is an invalid 'page' parameter key\")",
    "deep_paging_seite10000_size1_status": st_ok,
    "deep_paging_seite10000_erfolgreich": st_ok == 200 and bool(body_ok and json.loads(body_ok).get("data")),
    "deep_paging_seite10001_size1_status": st_fail,
    "deep_paging_seite10001_fehlermeldung": fehlermeldung_10001,
    "harte_grenze": "from+size <= 10000 (Elasticsearch index.max_result_window) — expliziter "
                    "HTTP-500-Fehler jenseits der Grenze, KEINE stille Leere",
}

# 5) Inkrement: sort=-modified (Anomalie-Test) + filter[modified] (echter Weg) ------
st, body, hdr = m.frag("sort_modified_desc_anomalie", API + "?page%5Bsize%5D=1&sort=-modified")
sort_status = st
time.sleep(PAUSE)
sort_anomalie = None
if body and st == 200:
    d = json.loads(body)
    if d.get("data"):
        a = d["data"][0]["attributes"]
        sort_anomalie = {"name": a.get("name"), "modified_epoch_ms": a.get("modified")}

st, body, hdr = m.frag("filter_modified_ungueltiges_format",
                       API + "?page%5Bsize%5D=1&filter%5Bmodified%5D=%5B2026-07-25T00%3A00%3A00Z%20TO%20%2A%5D")
time.sleep(PAUSE)
format_fehler = None
if body:
    try:
        format_fehler = json.loads(body).get("errors", [{}])[0].get("detail")
    except Exception:
        pass

heute = datetime.datetime.now(datetime.timezone.utc).strftime("%Y/%m/%d")
gestern = (datetime.datetime.now(datetime.timezone.utc)
           - datetime.timedelta(days=1)).strftime("%Y/%m/%d")

st, body, hdr = m.frag("inkrement_filter_modified_seit_heute",
                       API + f"?page%5Bsize%5D=1&filter%5Bmodified%5D={heute}")
seit_heute = json.loads(body).get("meta", {}).get("total") if body and st == 200 else None
time.sleep(PAUSE)

st, body, hdr = m.frag("inkrement_filter_modified_seit_gestern",
                       API + f"?page%5Bsize%5D=1&filter%5Bmodified%5D={gestern}")
seit_gestern = json.loads(body).get("meta", {}).get("total") if body and st == 200 else None

m.b["inkrement"] = {
    "weg": "filter[modified]=YYYY/MM/DD — KUMULATIV \"modified seit diesem Datum\", "
           "nicht \"an diesem Tag\" (belegt: filter=2020/01/01 lieferte 18.296.466, "
           "nahe am Gesamtbestand)",
    "filter_modified_format_hinweis": format_fehler,
    "sort_minus_modified_status": sort_status,
    "sort_minus_modified_top_record": sort_anomalie,
    "sort_minus_modified_anomalie": "Datenqualitätsproblem: 'neuestes' Record nach sort=-modified "
                                    "trägt ein Platzhalter-/Fehldatum weit in der Zukunft "
                                    "(epoch-ms >> heute) — sort=modified ist als Inkrement-Weg "
                                    "NICHT vertrauenswürdig, filter[modified] schon",
    "seit_heute_total": seit_heute,
    "seit_gestern_total": seit_gestern,
    "implizites_tagesvolumen_geschaetzt": (seit_gestern - seit_heute)
        if isinstance(seit_gestern, int) and isinstance(seit_heute, int) else None,
    "hinweis_tagesvolumen": "berechnet als seit_gestern_total - seit_heute_total aus zwei "
                            "gemessenen kumulativen Zählern; kein direkter Tageszähler vorhanden",
}

# 6) Effizienz: Sparse Fieldset (JSON:API fields[]) gegen den vollen Default-Payload ---
# Default-Records sind auffällig groß (siehe Rohdatei-Größe stichprobe_seite1); Test, ob
# JSON:API-Sparse-Fieldsets (fields[datasets]=...) unterstützt werden und wie stark das
# den Payload verkleinert — gleiche Seite 1, damit der Vergleich Datensatz-für-Datensatz gilt.
SPARSE_FELDER = ("name,owner,orgName,organization,source,url,license,structuredLicense,"
                 "modified,type,extent,itemExtent,metadata,itemId")
st, body, hdr = m.frag("sparse_fieldset_test",
                       API + f"?page%5Bsize%5D=100&page%5Bnumber%5D=1&fields%5Bdatasets%5D={SPARSE_FELDER}")
sparse_bytes = len(body) if body and st == 200 else None
if body and st == 200:
    m.roh("arcgis-sparse-fieldset-seite1.json.gz", body)
m.b["effizienz_sparse_fieldset"] = {
    "unterstuetzt": st == 200,
    "http_status": st,
    "bytes_default_seite1_100_records": seite1_bytes,
    "bytes_sparse_seite1_100_records": sparse_bytes,
    "einsparung_anteil": round(1 - sparse_bytes / seite1_bytes, 3)
        if sparse_bytes and seite1_bytes else None,
    "hinweis": "Default-Records bündeln das volle Feature-Service-Schema (layers/layer/fields/"
               "server/statistics) und werden dadurch pro Record sehr groß (Median dieser "
               "Stichprobe im zweistelligen KB-Bereich, einzelne Ausreißer > 8 MB pro Record); "
               "fields[datasets] reduziert den Payload drastisch, ohne die gemessenen "
               "Abdeckungsfelder zu verlieren.",
}

m.schreibe()
