#!/usr/bin/env python3
"""Erzeugt die Arbeitsvorlagen der Urteilsroutine — deterministisch, ohne Modell.

Zwei Vorlagen:

1. **Merge-Kandidaten.** Die automatischen Stufen R1–R4 führen nur zusammen, was
   belegt ist (gleiche PID, quellen-behauptete Relation, identisches Auflösungsziel).
   Alles darunter — insbesondere Titel-Ähnlichkeit — führt NIE automatisch zusammen
   (Design §1.2). Hier entsteht die Vorlage für den Fall, den ein Mensch oder ein
   Urteil entscheiden muss: **normalisierter Titel exakt gleich UND mindestens ein
   gemeinsamer Urheber oder gleicher Herausgeber**, aber noch nicht dieselbe Fassung.

2. **Stichprobe aus den Auto-Aufnahmen.** Alles automatisch Aufgenommene trägt
   `status: ungeprueft`. Eine Zufallsstichprobe wird zur Sichtung vorgelegt — das ist
   die Messung des Verfahrens gegen sich selbst.

Bereits beurteilte Paare werden übersprungen: Das Journal führt `merge` UND
`kein_merge`, damit dieselbe Frage nicht monatlich neu gestellt wird.
"""
import argparse
import itertools
import json
import random
import re
import sqlite3
import unicodedata

from hub_lib import BESTAND, JOURNAL, WURZEL, jetzt, jsonl_lesen

URTEIL = WURZEL / "urteil"


def normalisiere_titel(titel: str) -> str:
    """Kleinschreibung, Akzente weg, alles außer Buchstaben/Ziffern zu einem Leerzeichen.

    Bewusst grob: Diese Normalisierung entscheidet NICHTS, sie schlägt nur vor. Je
    großzügiger sie gruppiert, desto mehr Kandidaten sieht das Urteil — und desto
    weniger echte Dubletten bleiben unentdeckt liegen.
    """
    t = unicodedata.normalize("NFKD", titel or "").lower()
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", t)).strip()


def _urheber_namen(e: dict) -> set:
    return {(u.get("name") or "").strip().lower()
            for u in e.get("urheber") or [] if (u.get("name") or "").strip()}


def paar_schluessel(a: str, b: str) -> str:
    return "|".join(sorted((a, b)))


def lade(db):
    eintraege = {}
    for r in db.execute("SELECT id, fassung_id, werk_id, quelle, quell_id, titel, "
                        "herausgeber, publikationsjahr, zugang_url, status, json "
                        "FROM eintraege"):
        e = json.loads(r["json"])
        eintraege[r["id"]] = {
            "id": r["id"], "fassung_id": r["fassung_id"], "werk_id": r["werk_id"],
            "quelle": r["quelle"], "quell_id": r["quell_id"], "titel": r["titel"],
            "herausgeber": r["herausgeber"], "jahr": r["publikationsjahr"],
            "url": r["zugang_url"], "status": r["status"],
            "urheber": [u.get("name") for u in e.get("urheber") or []],
            "_urheber_norm": _urheber_namen(e),
        }
    return eintraege


def merge_kandidaten(eintraege, beurteilt):
    nach_titel = {}
    for e in eintraege.values():
        n = normalisiere_titel(e["titel"])
        if len(n) < 8:  # sehr kurze Titel ("data", "test") gruppieren zu wahllos
            continue
        nach_titel.setdefault(n, []).append(e)

    kandidaten = []
    for norm, gruppe in sorted(nach_titel.items()):
        # Gemessen am 2026-07-26 (17.327 Einträge): Bei Gruppen bis 25 entstanden
        # 9.906 Paare — fast ausschließlich Herbarbelege, bei denen hunderte
        # Datensätze denselben Titel (den Artnamen) und denselben Herausgeber tragen.
        # Das sind KEINE Dubletten, sondern verschiedene Exemplare derselben Art.
        # Der Urheber hilft nicht als Filter (der Sammler ist derselbe), die
        # Gruppengröße dagegen sehr: bis 5 bleiben 1.174 Paare, bis 3 noch 860 —
        # und die sehen tatsächlich nach Zweifelsfällen aus (aufeinanderfolgende
        # Zenodo-DOIs mit identischem Titel, gleiche Bezeichnung bei zwei ArcGIS-Items).
        # Ein Titel, der mehr als dreimal vorkommt, ist eine Serie, keine Dublette.
        if len(gruppe) < 2 or len(gruppe) > 3:
            continue
        for a, b in itertools.combinations(sorted(gruppe, key=lambda x: x["id"]), 2):
            if a["fassung_id"] == b["fassung_id"]:
                continue  # bereits durch R1–R4 zusammengeführt
            gemeinsame = a["_urheber_norm"] & b["_urheber_norm"]
            gleicher_herausgeber = (a["herausgeber"] and
                                    a["herausgeber"] == b["herausgeber"])
            if not (gemeinsame or gleicher_herausgeber):
                continue
            schluessel = paar_schluessel(a["id"], b["id"])
            if schluessel in beurteilt:
                continue
            kandidaten.append({
                "paar": schluessel,
                "normalisierter_titel": norm,
                "beleg": {
                    "gemeinsame_urheber": sorted(gemeinsame),
                    "gleicher_herausgeber": bool(gleicher_herausgeber),
                    "gleiches_werk_bereits": a["werk_id"] == b["werk_id"],
                },
                "eintraege": [
                    {k: x[k] for k in ("id", "quelle", "quell_id", "titel", "herausgeber",
                                       "jahr", "url", "urheber")}
                    for x in (a, b)
                ],
            })
    return kandidaten


def main(stichprobe_n: int, max_kandidaten: int, saat: int):
    URTEIL.mkdir(exist_ok=True)
    db = sqlite3.connect(BESTAND / "hub.sqlite")
    db.row_factory = sqlite3.Row
    eintraege = lade(db)
    db.close()

    journal = jsonl_lesen(JOURNAL / "entscheidungen.jsonl")
    beurteilt = set()
    for ereignis in journal:
        m = ereignis.get("mitglieder") or []
        if ereignis.get("typ") in ("merge", "kein_merge") and len(m) == 2:
            beurteilt.add(paar_schluessel(m[0], m[1]))

    kandidaten = merge_kandidaten(eintraege, beurteilt)
    gesamt = len(kandidaten)
    gekappt = max(0, gesamt - max_kandidaten)
    kandidaten = kandidaten[:max_kandidaten]

    (URTEIL / "kandidaten.jsonl").write_text(
        "".join(json.dumps(k, ensure_ascii=False) + "\n" for k in kandidaten))

    # Stichprobe: deterministisch über eine feste Saat, damit ein Lauf reproduzierbar
    # ist; die Saat kommt von außen (Datum), nicht aus dem Zufall der Maschine.
    ungeprueft = sorted([e["id"] for e in eintraege.values()
                         if e["status"] == "ungeprueft"])
    rng = random.Random(saat)
    gezogen = rng.sample(ungeprueft, min(stichprobe_n, len(ungeprueft)))
    (URTEIL / "stichprobe.jsonl").write_text("".join(
        json.dumps({k: eintraege[i][k] for k in
                    ("id", "quelle", "quell_id", "titel", "herausgeber", "jahr",
                     "url", "urheber", "status")}, ensure_ascii=False) + "\n"
        for i in gezogen))

    bericht = {
        "erzeugt": jetzt(),
        "eintraege_gesamt": len(eintraege),
        "merge_kandidaten_gefunden": gesamt,
        "merge_kandidaten_vorgelegt": len(kandidaten),
        "merge_kandidaten_gekappt": gekappt,
        "bereits_beurteilte_paare": len(beurteilt),
        "stichprobe": len(gezogen),
        "saat": saat,
    }
    (URTEIL / "vorlage.json").write_text(json.dumps(bericht, indent=2,
                                                    ensure_ascii=False) + "\n")
    print(json.dumps(bericht, indent=2, ensure_ascii=False))
    if gekappt:
        print(f"HINWEIS: {gekappt} Kandidaten wurden NICHT vorgelegt (Kappe "
              f"{max_kandidaten}). Sie verschwinden nicht — der nächste Lauf legt sie vor.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--stichprobe", type=int, default=15)
    p.add_argument("--max-kandidaten", type=int, default=40)
    p.add_argument("--saat", type=int, required=True,
                   help="Zufallssaat (z. B. YYYYMMDD) — macht den Lauf reproduzierbar")
    a = p.parse_args()
    main(a.stichprobe, a.max_kandidaten, a.saat)
