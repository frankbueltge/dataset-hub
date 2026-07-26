#!/usr/bin/env python3
"""Auflösungs-Budget: prüft Zugriffswege per HTTP (Design §2.2).

Liest Fundstellen, normalisiert, wählt bis zu --budget ungeprüfte Einträge
(neueste zuerst) und löst deren Zugriffs-URL tatsächlich auf. Ergebnisse landen
append-only in pruefungen/aufloesungen.jsonl. Ein Eintrag behauptet nie mehr,
als hier geprüft wurde.
"""
import argparse
import time

from hub_lib import FUNDSTELLEN, PRUEFUNGEN, hole, jetzt, jsonl_anhaengen, jsonl_gz_lesen, jsonl_lesen
from normalisiere import NORMALISIERER


def lade_eintraege():
    eintraege = {}
    for datei in sorted(FUNDSTELLEN.glob("*.jsonl.gz")):
        for fund in jsonl_gz_lesen(datei):
            f = NORMALISIERER.get(fund.get("quelle"))
            if not f:
                continue
            e = f(fund)
            alt = eintraege.get(e["id"])
            if not alt or fund.get("geerntet", "") > alt["fundstellen"][0].get("geerntet", ""):
                eintraege[e["id"]] = e
    return eintraege


def loese_auf(url: str):
    """HEAD zuerst (billig), aber jedem Nicht-2xx wird mit GET nachgegangen.

    HEAD ist im Web unzuverlässig implementiert: Kaggle etwa antwortet auf HEAD mit
    404 und auf GET mit 200 (gemessen 2026-07-26 — 400 Einträge waren dadurch
    fälschlich als nicht erreichbar vermerkt). Ein HEAD-Fehlschlag ist deshalb kein
    Befund über die Ressource, sondern nur über die Methode; erst das GET zählt.
    """
    status, _, _, finale = hole(url, timeout=20, versuche=1, accept="*/*",
                                methode="HEAD", koerper_lesen=False)
    if not (200 <= status < 300):
        status, _, _, finale = hole(url, timeout=25, versuche=1, accept="*/*",
                                    koerper_lesen=False)
    return status, finale


def main(budget: int, drossel: float, wiederholen: bool = False):
    pfad = PRUEFUNGEN / "aufloesungen.jsonl"
    # Letzter Stand je id — das Protokoll bleibt append-only, ein neuer Eintrag
    # überschreibt den alten nicht, sondern löst ihn ab (baue_bestand nimmt den letzten).
    letzte = {}
    for z in jsonl_lesen(pfad):
        letzte[z["id"]] = z
    if wiederholen:
        # Nur bestätigte Prüfungen überspringen: gescheiterte werden erneut versucht.
        # Nötig, wenn ein Fehler im Prüfverfahren selbst falsche Negative erzeugt hat.
        schon = {i for i, z in letzte.items() if z.get("ok")}
    else:
        schon = set(letzte)
    eintraege = lade_eintraege()
    kandidaten = [e for e in eintraege.values()
                  if e["id"] not in schon and e["zugang"]["url"]]
    kandidaten.sort(key=lambda e: e["fundstellen"][0].get("geerntet", ""), reverse=True)
    kandidaten = kandidaten[:budget]

    ok = fehler = ausfaelle = 0
    for e in kandidaten:
        eintrag = {"id": e["id"], "quelle": e["fundstellen"][0]["quelle"],
                   "quell_id": e["fundstellen"][0]["quell_id"],
                   "url": e["zugang"]["url"], "datum": jetzt()}
        try:
            status, finale = loese_auf(e["zugang"]["url"])
            eintrag.update({"http_status": status, "finale_url": finale,
                            "ok": 200 <= status < 300})
            ok += 1 if eintrag["ok"] else 0
            fehler += 0 if eintrag["ok"] else 1
        except RuntimeError as fehl:
            eintrag.update({"ausfall": str(fehl)[:300], "ok": False})
            ausfaelle += 1
        jsonl_anhaengen(pfad, eintrag)
        time.sleep(drossel)

    print(f"aufgelöst: {len(kandidaten)} (ok {ok}, nicht-2xx {fehler}, Ausfälle {ausfaelle}); "
          f"bereits geprüft: {len(schon)}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--budget", type=int, default=200)
    p.add_argument("--drossel", type=float, default=0.3)
    p.add_argument("--wiederholen", action="store_true",
                   help="gescheiterte Prüfungen erneut versuchen (bestätigte bleiben)")
    a = p.parse_args()
    main(a.budget, a.drossel, a.wiederholen)
