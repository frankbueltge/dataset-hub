#!/usr/bin/env python3
"""Ernte-Adapter HuggingFace Datasets: Cursor via Link-Header, `full=true`.

Besonderheit — dokumentierte Quellen-Ausnahme (schema/SCHEMA.md, Abschnitt
"Quellen-Ausnahme"; Messung messungen/ergebnisse/2026-07-26-huggingface.md,
Abschnitt 6): die API führt KEIN URL-Feld. Der Zugriffsweg wird darum NICHT hier
in der Ernte konstruiert, sondern erst beim Normalisieren (normalisiere.py:
normalisiere_huggingface) — die Fundstelle bleibt roh = Quellrecord wörtlich,
unverändert (Schema verbietet zusätzliche Felder in der Fundstelle). Die Pflicht-
Auflösung per HTTP VOR jeder Aufnahme wird technisch in schranken.py erzwungen
(Grundcode `konstruierte-url-ungeprueft`) und läuft über den bestehenden,
quellen-unabhängigen Auflösungs-Schritt (pipeline/aufloese.py); dieser Adapter
macht dazu keine zusätzlichen synchronen HTTP-Aufrufe pro Record.

Diese Ernte selbst ist ein reiner Listen-Abzug (keine Volliteration bis zum Ende
nötig für einen Testlauf) — Cursor-Volliteration ist laut Messung technisch
belegt (120 Seiten à 1.000 ohne Fehler), wird hier aber wie bei den anderen
Adaptern über `--max-seiten` gekappt, damit ein Testlauf billig bleibt.
"""
import argparse
import gzip
import json
import time

from hub_lib import FUNDSTELLEN, MANIFESTE, hole, jetzt, sha256_datei, vermerk_ausfall

ADAPTER_VERSION = "0.1.0"
API = "https://huggingface.co/api/datasets"
DROSSEL = 0.25


def _naechste_url(link_header: str):
    """Parst einen RFC-5988-artigen Link-Header (`<url>; rel="next"`) analog zu
    GitHubs Paginierung. Gibt None zurück, wenn kein rel="next" vorhanden ist."""
    if not link_header:
        return None
    for teil in link_header.split(","):
        stuecke = teil.split(";")
        if len(stuecke) < 2:
            continue
        url = stuecke[0].strip().strip("<>")
        for attribut in stuecke[1:]:
            if attribut.strip().replace(" ", "") == 'rel="next"':
                return url
    return None


def ernte(max_seiten: int, limit: int):
    FUNDSTELLEN.mkdir(exist_ok=True)
    MANIFESTE.mkdir(parents=True, exist_ok=True)
    start = jetzt()
    lauf = f"huggingface-{start.replace(':', '').replace('-', '')}"
    datei = FUNDSTELLEN / f"{lauf}.jsonl.gz"

    url = f"{API}?full=true&limit={limit}"
    seiten, records, vollstaendig = 0, 0, True
    hinweis = None

    with gzip.open(datei, "wt", encoding="utf-8") as f:
        while url and seiten < max_seiten:
            try:
                status, body, header, _ = hole(url, timeout=90)
            except RuntimeError as e:
                vermerk_ausfall("huggingface", lauf, e, kontext=f"Seite {seiten + 1}")
                vollstaendig = False
                hinweis = f"Netzausfall bei Seite {seiten + 1}"
                break
            if status != 200:
                vermerk_ausfall("huggingface", lauf, f"HTTP {status}",
                                kontext=f"Seite {seiten + 1}: {body[:200]!r}")
                vollstaendig = False
                hinweis = f"HTTP {status} bei Seite {seiten + 1}"
                break
            daten = json.loads(body)
            if not daten:
                break
            for rec in daten:
                hf_id = rec.get("id") or ""
                f.write(json.dumps({
                    "quelle": "huggingface",
                    "quell_id": hf_id,
                    "geerntet": jetzt(),
                    "adapter_version": ADAPTER_VERSION,
                    "roh": rec,
                }, ensure_ascii=False) + "\n")
                records += 1
            seiten += 1
            url = _naechste_url(header.get("link"))
            time.sleep(DROSSEL)

    if vollstaendig and url and seiten >= max_seiten:
        vollstaendig = False
        hinweis = "Seitenkappe erreicht, weitere Seiten möglich (Cursor vorhanden)"
        vermerk_ausfall("huggingface", lauf, "Seitenkappe erreicht",
                        kontext=f"max_seiten={max_seiten}")

    manifest = {
        "lauf": lauf, "quelle": "huggingface", "adapter_version": ADAPTER_VERSION,
        "bis": jetzt(), "seiten": seiten, "records": records, "limit": limit,
        "vollstaendig": vollstaendig, "hinweis": hinweis,
        "datei": datei.name, "sha256": sha256_datei(datei),
    }
    (MANIFESTE / f"{lauf}.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return manifest


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--max-seiten", type=int, default=3)
    p.add_argument("--limit", type=int, default=100,
                   help="Records/Seite (Standard klein für billige Testläufe; "
                        "Messung nutzte 1000)")
    a = p.parse_args()
    ernte(a.max_seiten, a.limit)
