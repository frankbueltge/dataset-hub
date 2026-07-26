#!/usr/bin/env python3
"""Ernte-Adapter Kaggle (unauthentifiziert): page=N, sortBy=updated, 20/Seite.

Auflagen aus der Messung (messungen/ergebnisse/2026-07-26-kaggle.md), bindend:

(1) In 2 von 3 Messläufen brach die Seiten-Iteration mit unangekündigtem HTTP 404
    mitten in der Sequenz ab (kein Rate-Limit-Header, kein 429). Ein 404 ist darum
    NIE das Ende der Iteration: die betroffene Seite wird nach Pause erneut
    versucht; hält der Fehler an, wird ein Ausfall vermerkt und der Lauf als
    unvollständig markiert (statt so zu tun, als sei der Bestand erschöpft).
(2) Stilles Fenster bei exakt 10.000 erreichbaren Records (Seite 501 liefert HTTP
    200 mit leerem Array — kein Fehler, keine Ankündigung). Eine leere Seite ist
    deshalb NIE ein Beweis für Vollständigkeit; sie wird im Manifest als
    Unvollständigkeit mit Begründung vermerkt.
(3) Inkrement über `sortBy=updated` (dokumentierter, tatsächlich geprüfter Query-
    Parameter) — für den laufenden Betrieb ausreichend, ohne echtes Zeitfenster.

Schreibt Fundstellen wörtlich (roh = Quellrecord unverändert) als JSONL.gz plus
Manifest mit Zähler, SHA-256 und Vollständigkeits-Flag.
"""
import argparse
import gzip
import json
import time

from hub_lib import FUNDSTELLEN, MANIFESTE, hole, jetzt, sha256_datei, vermerk_ausfall

ADAPTER_VERSION = "0.1.0"
API = "https://www.kaggle.com/api/v1/datasets/list"
SEITENGROESSE = 20  # von Kaggle fix vorgegeben, kein page[size]-Parameter bekannt
DROSSEL = 0.5
NEUVERSUCHE_404 = 3
PAUSE_404 = 3.0


def _seite_holen(seite: int):
    """Holt eine Seite. hole() deckt bereits 429/502/503 (eingebaute Retries) ab;
    zusätzlich hier: Pause + Wiederholung speziell für das unangekündigte HTTP 404
    aus der Messung, das kein Standard-Fehlercode für "Ende" ist."""
    url = f"{API}?page={seite}&sortBy=updated"
    status, body = None, b""
    for versuch in range(NEUVERSUCHE_404 + 1):
        status, body, _, _ = hole(url, timeout=60)
        if status == 404 and versuch < NEUVERSUCHE_404:
            time.sleep(PAUSE_404 * (versuch + 1))
            continue
        break
    return status, body


def ernte(max_seiten: int):
    FUNDSTELLEN.mkdir(exist_ok=True)
    MANIFESTE.mkdir(parents=True, exist_ok=True)
    start = jetzt()
    lauf = f"kaggle-{start.replace(':', '').replace('-', '')}"
    datei = FUNDSTELLEN / f"{lauf}.jsonl.gz"

    seiten, records, vollstaendig = 0, 0, True
    hinweis = None

    with gzip.open(datei, "wt", encoding="utf-8") as f:
        seite = 1
        while seiten < max_seiten:
            status, body = _seite_holen(seite)
            if status == 404:
                vermerk_ausfall("kaggle", lauf, "HTTP 404 nach Wiederholungen (Auflage 1)",
                                kontext=f"Seite {seite}")
                vollstaendig = False
                hinweis = f"unangekündigtes HTTP 404 bei Seite {seite}, auch nach Retry"
                break
            if status != 200:
                vermerk_ausfall("kaggle", lauf, f"HTTP {status}",
                                kontext=f"Seite {seite}: {body[:200]!r}")
                vollstaendig = False
                hinweis = f"HTTP {status} bei Seite {seite}"
                break
            try:
                daten = json.loads(body)
            except json.JSONDecodeError as e:
                vermerk_ausfall("kaggle", lauf, f"kein gueltiges JSON: {e}",
                                kontext=f"Seite {seite}")
                vollstaendig = False
                hinweis = f"ungültiges JSON bei Seite {seite}"
                break
            if not daten:
                # Auflage 2: stille Leere ist NIE ein Vollständigkeitsbeweis —
                # identisches Muster wie das ArcGIS-Hub-10k-Fenster, nur ohne
                # expliziten Fehlercode.
                vollstaendig = False
                hinweis = (f"leere Seite {seite} (HTTP 200, leeres Array) — "
                           "kein Vollständigkeitsbeweis, moegliches 10k-Fenster")
                break
            for rec in daten:
                ref = rec.get("ref") or ""
                f.write(json.dumps({
                    "quelle": "kaggle",
                    "quell_id": ref,
                    "geerntet": jetzt(),
                    "adapter_version": ADAPTER_VERSION,
                    "roh": rec,
                }, ensure_ascii=False) + "\n")
                records += 1
            seiten += 1
            seite += 1
            time.sleep(DROSSEL)

    if vollstaendig and seiten >= max_seiten:
        vollstaendig = False
        hinweis = "Seitenkappe erreicht, weitere Seiten möglich"
        vermerk_ausfall("kaggle", lauf, "Seitenkappe erreicht",
                        kontext=f"max_seiten={max_seiten}")

    manifest = {
        "lauf": lauf, "quelle": "kaggle", "adapter_version": ADAPTER_VERSION,
        "bis": jetzt(), "seiten": seiten, "records": records,
        "seitengroesse": SEITENGROESSE, "vollstaendig": vollstaendig,
        "hinweis": hinweis,
        "datei": datei.name, "sha256": sha256_datei(datei),
    }
    (MANIFESTE / f"{lauf}.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return manifest


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--max-seiten", type=int, default=3)
    a = p.parse_args()
    ernte(a.max_seiten)
