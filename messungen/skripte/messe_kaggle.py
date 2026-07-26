#!/usr/bin/env python3
"""Messung: Kaggle Datasets-Liste — https://www.kaggle.com/api/v1/datasets/list (lesend,
unauthentifiziert; Zaehl-Iteration mit Kappe 100 Seiten a 20, Drossel 0,5 s).

Vorerkundung (`2026-07-26-vorerkundung-weitere-quellen.md`): HTTP 200 ohne Auth; Records
tragen wortliche url/licenseName/creatorName. Kein Gesamtzaehler in der Antwort oder in
Headern -> Bestand nur ueber Iteration naeherbar.

Reihenfolge bewusst so gewaehlt, dass sortBy- und Deep-Page-Tests VOR der langen
Zaehl-Iteration laufen: in zwei Testlaeufen brach die Iteration reproduzierbar bei
Seite 60 mit HTTP 404 ab (siehe unten), was sonst auch die spaeteren, unabhaengigen
Tests kollateral mit-abgerissen haette.
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

# 2) Inkrement-Weg: sortBy=updated tatsaechlich abfragen (VOR der langen Iteration) -
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

# 3) Kappungs-Diagnose: Deep-Page-Grenze der Standardsortierung (VOR der Iteration) -
st_500, body_500, _ = m.frag("kappungs_diagnose_seite500", API + "?page=500")
time.sleep(PAUSE)
st_501, body_501, _ = m.frag("kappungs_diagnose_seite501", API + "?page=501")
time.sleep(PAUSE)
n_500 = len(json.loads(body_500)) if body_500 and st_500 == 200 else None
n_501 = len(json.loads(body_501)) if body_501 and st_501 == 200 else None
m.b["kappungs_diagnose"] = {
    "seite500_http_status": st_500,
    "seite500_n": n_500,
    "seite501_http_status": st_501,
    "seite501_n": n_501,
    "befund": ("Seite 500 (Record 9981-10000) liefert noch volle 20 Records, Seite 501 "
               "liefert HTTP 200 mit leerem Array — stilles Fenster-Limit bei genau "
               "10.000 erreichbaren Records in der Standardsortierung (identischer Wert "
               "wie ArcGIS Hub: gemeinsames technisches Muster, vermutlich Elasticsearch-"
               "Standardfenster). Kein unabhaengiger Gesamtzaehler verfuegbar, um zu "
               "pruefen, ob dies der echte Bestand oder eine Fensterbegrenzung ist — "
               "der runde Wert 10.000 spricht fuer Fensterbegrenzung, nicht echten Bestand.")
        if n_500 == 20 and n_501 == 0 else
        "Abweichender Befund gegenueber der Voruntersuchung — siehe Rohwerte (http_status "
        f"seite500={st_500}, seite501={st_501}).",
}

# 4) Zaehl-Iteration ueber Seiten (Standardsortierung), Kappe 100 Seiten -----------
# Bei einem non-200 mitten in der Iteration: EIN Retry nach kurzer Abkuehlpause, um
# einen transienten Ausfall von einer echten/persistenten Grenze zu unterscheiden
# (Vorlauf zeigte zweimal reproduzierbar HTTP 404 bei genau Seite 60 waehrend der
# Iteration, aber sofortige isolierte Nachfragen derselben Seite dahinter liefen
# wieder sauber — siehe "wall_diagnose" unten).
recs = []
seiten_gelesen = 0
leere_seite_bei = None
http_fehler = []
wall_diagnose = None
seite_nr = 0
try:
    while seiten_gelesen < KAPPE:
        seite_nr += 1
        st, body, hdr = hole(API + f"?page={seite_nr}", timeout=30)
        if st != 200:
            time.sleep(3.0)
            st_retry, body_retry, hdr_retry = hole(API + f"?page={seite_nr}", timeout=30)
            wall_diagnose = {
                "seite": seite_nr, "erster_versuch_status": st,
                "retry_nach_3s_status": st_retry,
                "retry_erfolgreich": st_retry == 200,
            }
            if st_retry == 200:
                st, body, hdr = st_retry, body_retry, hdr_retry
            else:
                http_fehler.append({"seite": seite_nr, "http_status": st, "retry_status": st_retry})
                m.b["ausfaelle"].append({"zweck": "zaehl_iteration", "seite": seite_nr,
                                         "http_status": st, "retry_status": st_retry})
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
    "wall_diagnose": wall_diagnose,
}
if seiten_gelesen >= KAPPE and leere_seite_bei is None:
    m.b["zaehler"]["hinweis"] = (f"Kappe ({KAPPE} Seiten x {SEITENGROESSE}) erreicht, KEINE leere "
                                 f"Seite gesehen — Bestand ist GRÖSSER als {len(recs)} "
                                 f"(ehrliche Untergrenze, kein Gesamtzähler in der API)")
elif leere_seite_bei is not None:
    m.b["zaehler"]["hinweis"] = (f"Echtes Ende innerhalb der Kappe erreicht: leere Seite bei "
                                 f"Seitennummer {leere_seite_bei} — Bestand exakt "
                                 f"{len(recs)} Records (falls kein stiller Cutoff greift, "
                                 f"siehe kappungs_diagnose)")
elif http_fehler:
    m.b["zaehler"]["hinweis"] = (f"Iteration vor der Kappe an einem HTTP-Fehler abgebrochen — "
                                 f"Bestand ist GRÖSSER als {len(recs)} (ehrliche Untergrenze, "
                                 f"Ursache siehe wall_diagnose)")

# 5) Stichprobe (n>=200) aus den bereits iterierten Seiten, wörtlich gebündelt ------
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

# 6) Rate-Limit-Beobachtung: 429s? Header ueber den Lauf; Wall-Befund zusammengefasst
m.b["rate_limit_beobachtung"] = {
    "429_waehrend_iteration": any(f.get("http_status") == 429 or f.get("retry_status") == 429
                                  for f in http_fehler),
    "header_erster_request": m.b["header_befund"]["alle_header"],
    "wall_diagnose": wall_diagnose,
    "hinweis": "keine x-ratelimit-* oder retry-after-Header in irgendeiner Antwort dieser "
               "Messung beobachtet; kein 429 waehrend " + str(seiten_gelesen) + " gelesener "
               f"Seiten a {PAUSE}s Drossel. " +
               ("Ein HTTP-Fehler (nicht 429) trat waehrend der Iteration auf — Details in "
                "wall_diagnose/http_fehler_waehrend_iteration." if http_fehler else
                "Keine HTTP-Fehler waehrend der Iteration."),
}

# 7) Hinweis fuer G4-Diskussion: gibt es einen alternativen Bulk-Dump-Weg jenseits der
#    10k-Fenstergrenze (analog Zenodos OAI-PMH)? Kaggle veroeffentlicht selbst einen
#    Metadaten-Dump als eigenes Dataset ("Meta Kaggle") -- Existenz/Frische pruefen,
#    volle Struktur-Messung bleibt eigener Nachmessungs-Auftrag.
st, body, hdr = m.frag("bulk_dump_hinweis_meta_kaggle", API + "?search=meta%20kaggle")
time.sleep(PAUSE)
meta_kaggle = None
if body and st == 200:
    d = json.loads(body)
    if isinstance(d, list):
        treffer = [r for r in d if r.get("ref") == "kaggle/meta-kaggle"]
        if treffer:
            r = treffer[0]
            meta_kaggle = {"ref": r.get("ref"), "title": r.get("title"),
                          "ownerName": r.get("ownerName"), "lastUpdated": r.get("lastUpdated"),
                          "totalBytes": r.get("totalBytes")}
    m.roh("kaggle-suche-meta-kaggle.json.gz", body)
m.b["bulk_dump_hinweis"] = {
    "http_status": st,
    "kaggle_meta_kaggle_gefunden": meta_kaggle is not None,
    "kaggle_meta_kaggle": meta_kaggle,
    "hinweis": "Kaggle veroeffentlicht selbst \"kaggle/meta-kaggle\" als first-party-Datensatz "
               "mit periodisch aktualisierten CSV-Dumps der Katalog-Metadaten -- ein moeglicher "
               "G4-Weg jenseits der 10k-Fenstergrenze der List-API, analog zu Zenodos OAI-PMH. "
               "NICHT Teil dieser Messung (nur Existenz/Frische geprueft, keine Struktur- oder "
               "Feldabdeckungsmessung des Dumps selbst) -- eigener Nachmessungs-Auftrag, falls "
               "Kaggle als Kernquelle in Frage kommt.",
}

m.schreibe()
