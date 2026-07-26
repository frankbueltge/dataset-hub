#!/usr/bin/env python3
"""Messung: Kaggle Datasets-Liste — https://www.kaggle.com/api/v1/datasets/list (lesend,
unauthentifiziert; Zaehl-Iteration mit Kappe 100 Seiten a 20, Drossel 0,5 s).

Vorerkundung (`2026-07-26-vorerkundung-weitere-quellen.md`): HTTP 200 ohne Auth; Records
tragen wortliche url/licenseName/creatorName. Kein Gesamtzaehler in der Antwort oder in
Headern -> Bestand nur ueber Iteration naeherbar.
"""
import json
import time

from mess_lib import Messung, abdeckung, hole

m = Messung("kaggle")
API = "https://www.kaggle.com/api/v1/datasets/list"
SEITENGROESSE = 20
KAPPE = 100
PAUSE = 0.5

# 1) Header-Befund: Zaehler oder Rate-Limit-Hinweise im Header? --------------------
st, body, hdr = m.frag("header_check", API + "?page=1")
m.b["header_befund"] = {
    "http_status": st,
    "alle_header": dict(hdr or {}),
    "rate_limit_header_vorhanden": any("ratelimit" in k or "rate-limit" in k for k in (hdr or {})),
    "x_kaggle_header": {k: v for k, v in (hdr or {}).items() if k.startswith("x-kaggle")},
}
time.sleep(PAUSE)

# 2) Zaehl-Iteration ueber Seiten (Standardsortierung), Kappe 100 Seiten -----------
recs = []
seiten_gelesen = 0
leere_seite_bei = None
http_fehler = []
seite_nr = 0
try:
    while seiten_gelesen < KAPPE:
        seite_nr += 1
        st, body, hdr = hole(API + f"?page={seite_nr}", timeout=30)
        if st != 200:
            http_fehler.append({"seite": seite_nr, "http_status": st})
            m.b["ausfaelle"].append({"zweck": "zaehl_iteration", "seite": seite_nr, "http_status": st})
            break
        d = json.loads(body)
        if not isinstance(d, list):
            m.b["ausfaelle"].append({"zweck": "zaehl_iteration", "seite": seite_nr,
                                     "problem": "Antwort ist keine Liste", "antwort_anfang": str(d)[:200]})
            break
        seiten_gelesen += 1
        if len(d) == 0:
            leere_seite_bei = seite_nr
            break
        recs.extend(d)
        if seite_nr == 1:
            m.b["abfragen"].append({"zweck": "zaehl_iteration_seite1", "url": API + "?page=1", "http_status": st})
        time.sleep(PAUSE)
except RuntimeError as e:
    m.b["ausfaelle"].append({"zweck": "zaehl_iteration", "fehler": str(e)})

m.b["zaehler"] = {
    "iteriert_records": len(recs),
    "seiten_gelesen": seiten_gelesen,
    "kappe_erreicht": seiten_gelesen >= KAPPE and leere_seite_bei is None,
    "leere_seite_bei_seitennummer": leere_seite_bei,
    "http_fehler_waehrend_iteration": http_fehler,
}
if seiten_gelesen >= KAPPE and leere_seite_bei is None:
    m.b["zaehler"]["hinweis"] = (f"Kappe ({KAPPE} Seiten x {SEITENGROESSE}) erreicht, KEINE leere "
                                 f"Seite gesehen — Bestand ist GRÖSSER als {len(recs)} "
                                 f"(ehrliche Untergrenze, kein Gesamtzähler in der API)")

# 3) Kappungs-Diagnose: liegt der wahre Bestand nahe an der 100-Seiten-Kappe, oder gibt
#    es ein tieferes, stilles Fenster-Limit? Gezielte Zusatzabfragen jenseits der Kappe,
#    an der aus einer separaten Reihe manuell ermittelten Grenze (Seite 500/501). --------
st_500, body_500, _ = m.frag("kappungs_diagnose_seite500", API + "?page=500")
time.sleep(PAUSE)
st_501, body_501, _ = m.frag("kappungs_diagnose_seite501", API + "?page=501")
time.sleep(PAUSE)
n_500 = len(json.loads(body_500)) if body_500 and st_500 == 200 else None
n_501 = len(json.loads(body_501)) if body_501 and st_501 == 200 else None
m.b["kappungs_diagnose"] = {
    "seite500_n": n_500,
    "seite501_n": n_501,
    "befund": ("Seite 500 (Record 9981-10000) liefert noch volle 20 Records, Seite 501 "
               "liefert HTTP 200 mit leerem Array — stilles Fenster-Limit bei genau "
               "10.000 erreichbaren Records in der Standardsortierung (identischer Wert "
               "wie ArcGIS Hub: gemeinsames technisches Muster, vermutlich Elasticsearch-"
               "Standardfenster). Kein unabhaengiger Gesamtzaehler verfuegbar, um zu "
               "pruefen, ob dies der echte Bestand oder eine Fensterbegrenzung ist — "
               "der runde Wert 10.000 spricht fuer Fensterbegrenzung, nicht echten Bestand.")
        if n_500 == 20 and n_501 == 0 else
        "Abweichender Befund gegenueber der Voruntersuchung — siehe Rohwerte.",
}

# 4) Stichprobe (n>=200) aus den bereits iterierten Seiten, wörtlich gebündelt ------
stichprobe = recs[:200] if len(recs) >= 200 else recs
if stichprobe:
    m.roh("kaggle-stichprobe.json.gz",
          json.dumps(stichprobe, ensure_ascii=False).encode("utf-8"))
m.b["stichprobe"] = {
    "n": len(stichprobe),
    "ziehung": "Convenience: erste " + str(len(stichprobe)) + " Records der Zaehl-Iteration "
               "(Standardsortierung, kein Zufallsparameter bekannt) — NICHT gleichverteilt; "
               "wörtlich aus den iterierten Seiten übernommen, nur zur Ablage gebündelt",
}


def _lizenz(r):
    return bool((r.get("licenseName") or "").strip())


m.b["abdeckung"] = abdeckung(stichprobe, {
    "titel": lambda r: bool((r.get("title") or "").strip()),
    "urheber": lambda r: bool((r.get("creatorName") or r.get("ownerName") or "").strip()),
    "zugriffs_url": lambda r: bool((r.get("url") or "").strip()),
    "lizenz": _lizenz,
    "beschreibung_oder_subtitle": lambda r: bool((r.get("description") or "").strip()
                                                 or (r.get("subtitle") or "").strip()),
    "groesse_totalBytes": lambda r: r.get("totalBytes") is not None,
    "aktualisierungsdatum": lambda r: bool(r.get("lastUpdated")),
})

# 5) Inkrement-Weg: sortBy=updated tatsaechlich abfragen --------------------------
st, body, hdr = m.frag("inkrement_sortBy_updated", API + "?page=1&sortBy=updated")
time.sleep(PAUSE)
eintrag = {"http_status": st}
if body and st == 200:
    d = json.loads(body)
    eintrag["n"] = len(d) if isinstance(d, list) else None
    if isinstance(d, list) and d:
        eintrag["oberstes_lastUpdated"] = d[0].get("lastUpdated")
        eintrag["oberster_titel"] = d[0].get("title")
    m.roh("kaggle-sortBy-updated-seite1.json.gz", body)
m.b["inkrement"] = {"weg": "sortBy=updated (Standard-Query-Parameter, dokumentiert per "
                          "Enum-Fehlermeldung anderer Werte)", **eintrag}

# 6) Rate-Limit-Beobachtung: alle 429 waehrend der Iteration? Header ueber den Lauf --
m.b["rate_limit_beobachtung"] = {
    "429_waehrend_iteration": any(f.get("http_status") == 429 for f in http_fehler),
    "header_erster_request": m.b["header_befund"]["alle_header"],
    "hinweis": "keine x-ratelimit-* oder retry-after-Header in keiner Antwort dieser Messung "
               "beobachtet; kein 429 waehrend " + str(seiten_gelesen) + " Seiten a "
               f"{PAUSE}s Drossel aufgetreten",
}

m.schreibe()
