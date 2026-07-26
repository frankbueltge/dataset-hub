#!/usr/bin/env python3
"""Bulk-Bootstrap aus dem DataCite Public Data File — im Strom, ohne Zwischenablage.

Das Archiv ist ein TAR mit Monatsordnern (`dois/updated_YYYY-MM/part_NNNN.jsonl.gz`),
33 GiB gepackt, 615 GiB entpackt, 108,5 Mio. Records aller Ressourcenarten. Beides
passt nicht auf eine normale Platte — deshalb wird es NIE abgelegt und nie vollständig
entpackt, sondern direkt aus der HTTP-Antwort gelesen:

    HTTP-Strom → tarfile(mode='r|') → gzip je Mitglied → JSONL-Zeilen → Filter → Ausgabe

Geschrieben werden nur Fundstellen vom Typ `dataset`, im selben Format wie die
Ernte-Adapter. Der Lauf ist jederzeit abbrechbar; was geschrieben wurde, bleibt gültig,
und das Manifest sagt ehrlich, wie weit er gekommen ist.

Zugang: Der Download-Link ist personengebunden und 24 h gültig. Er wird NICHT im Repo
abgelegt, sondern als Umgebungsvariable übergeben:

    DATACITE_DUMP_URL="https://…" python3 importiere_datacite_dump.py --messen
"""
import argparse
import gzip
import shutil
import io
import json
import os
import sys
import tarfile
import time
import urllib.request

from hub_lib import FUNDSTELLEN, MANIFESTE, UA, jetzt, normalisiere_doi, sha256_datei

ADAPTER_VERSION = "0.1.0-dump2025"
# Nur diese Ressourcenart wird aufgenommen — die Datei enthält alle (Text, Software,
# Image …). Der Wert steht in attributes.types.resourceTypeGeneral.
GESUCHTE_ART = "Dataset"


def oeffne_strom(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=120)


# Sicherheitsgrenze: Der Lauf schreibt viele Stunden lang. Läuft die Platte voll,
# stünde am Ende ein halb geschriebener Bestand UND ein blockiertes System. Deshalb
# beendet er sich vorher selbst — und vermerkt das im Manifest, statt still aufzuhören.
FREIER_SPEICHER_MINIMUM = 15 * 1024**3


def genug_platz() -> bool:
    return shutil.disk_usage(FUNDSTELLEN).free > FREIER_SPEICHER_MINIMUM


def menschlich(n: float) -> str:
    for e in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {e}"
        n /= 1024
    return f"{n:.1f} PB"


def main(url: str, max_records: int | None, nur_messen: bool, teilgroesse: int):
    FUNDSTELLEN.mkdir(exist_ok=True)
    MANIFESTE.mkdir(parents=True, exist_ok=True)
    start = jetzt()
    lauf = f"datacite-dump-{start.replace(':', '').replace('-', '')}"

    gelesen = geschrieben = teile = 0
    bytes_gelesen = 0
    mitglieder = 0
    letzter_monat = ""
    dateien = []
    ausgabe = None
    t0 = time.time()

    def neue_ausgabe():
        nonlocal ausgabe, teile
        if ausgabe:
            ausgabe.close()
        name = f"{lauf}-teil{teile:04d}.jsonl.gz"
        dateien.append(name)
        teile += 1
        return gzip.open(FUNDSTELLEN / name, "wt", encoding="utf-8")

    if not nur_messen:
        ausgabe = neue_ausgabe()
        in_teil = 0

    strom = oeffne_strom(url)
    # mode='r|' = reiner Vorwärtsstrom: tarfile springt nie zurück, es wird also
    # nichts gepuffert, was nicht gerade gebraucht wird.
    tar = tarfile.open(fileobj=strom, mode="r|")
    try:
        for mitglied in tar:
            if not mitglied.name.endswith(".jsonl.gz"):
                continue
            mitglieder += 1
            monat = mitglied.name.split("/")[1] if "/" in mitglied.name else ""
            if monat != letzter_monat:
                letzter_monat = monat
                verstrichen = time.time() - t0
                print(f"  {monat}  gelesen {gelesen:>12,}  aufgenommen {geschrieben:>12,}  "
                      f"{menschlich(bytes_gelesen)}  {verstrichen/60:.1f} min", flush=True)
            f = tar.extractfile(mitglied)
            if f is None:
                continue
            bytes_gelesen += mitglied.size
            with gzip.open(io.BytesIO(f.read()), "rt", encoding="utf-8") as roh:
                for zeile in roh:
                    zeile = zeile.strip()
                    if not zeile:
                        continue
                    gelesen += 1
                    try:
                        rec = json.loads(zeile)
                    except json.JSONDecodeError:
                        continue  # defekte Zeile: überspringen, unten gezählt
                    attr = rec.get("attributes") or rec
                    art = ((attr.get("types") or {}).get("resourceTypeGeneral") or "")
                    if art != GESUCHTE_ART:
                        continue
                    geschrieben += 1
                    if nur_messen:
                        if max_records and gelesen >= max_records:
                            raise StopIteration
                        continue
                    ausgabe.write(json.dumps({
                        "quelle": "datacite",
                        "quell_id": normalisiere_doi(attr.get("doi") or rec.get("id")),
                        "geerntet": jetzt(),
                        "adapter_version": ADAPTER_VERSION,
                        "roh": attr,
                    }, ensure_ascii=False) + "\n")
                    in_teil += 1
                    if in_teil >= teilgroesse:
                        ausgabe = neue_ausgabe()
                        in_teil = 0
                        if not genug_platz():
                            print("\n  ABBRUCH: weniger als 15 GB frei — Lauf beendet, "
                                  "geschriebene Teile bleiben gültig", flush=True)
                            raise StopIteration
                    if max_records and gelesen >= max_records:
                        raise StopIteration
    except StopIteration:
        vollstaendig = False
    except KeyboardInterrupt:
        print("\n  abgebrochen — bereits geschriebene Teile bleiben gültig", flush=True)
        vollstaendig = False
    else:
        vollstaendig = True
    finally:
        try:
            tar.close()
        except Exception:
            pass
        strom.close()
        if ausgabe:
            ausgabe.close()

    dauer = time.time() - t0
    manifest = {
        "lauf": lauf, "quelle": "datacite", "adapter_version": ADAPTER_VERSION,
        "weg": "public data file 2025 (tar-Strom, gefiltert auf Typ dataset)",
        "seit": "(Altbestand bis Ende 2025)", "bis": jetzt(),
        "records_gelesen": gelesen, "records": geschrieben,
        "mitglieder": mitglieder, "vollstaendig": vollstaendig,
        "dauer_minuten": round(dauer / 60, 1),
        "dateien": dateien,
    }
    if not vollstaendig:
        manifest["hinweis"] = ("Lauf vorzeitig beendet (Kappe oder Abbruch) — der "
                               "Altbestand ist unvollständig eingelesen.")
    if not nur_messen and dateien:
        manifest["sha256"] = {d: sha256_datei(FUNDSTELLEN / d) for d in dateien}
        bytes_aus = sum((FUNDSTELLEN / d).stat().st_size for d in dateien)
        manifest["bytes_geschrieben"] = bytes_aus
        manifest["bytes_je_eintrag"] = round(bytes_aus / geschrieben, 1) if geschrieben else None
        (MANIFESTE / f"{lauf}.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    print(json.dumps({k: v for k, v in manifest.items() if k != "sha256"},
                     indent=2, ensure_ascii=False))
    if nur_messen:
        anteil = geschrieben / gelesen if gelesen else 0
        print(f"\nMESSUNG: {gelesen:,} Records gelesen, davon {geschrieben:,} vom Typ "
              f"dataset ({anteil:.1%}). Hochrechnung auf 108,5 Mio. Records: "
              f"rund {int(108_468_906 * anteil):,} Datensätze.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--max-records", type=int, default=None,
                   help="nach so vielen GELESENEN Records aufhören (Messläufe)")
    p.add_argument("--messen", action="store_true",
                   help="nichts schreiben, nur zählen und hochrechnen")
    p.add_argument("--teilgroesse", type=int, default=500_000,
                   help="Fundstellen je Ausgabedatei")
    a = p.parse_args()
    url = os.environ.get("DATACITE_DUMP_URL")
    if not url:
        sys.exit("DATACITE_DUMP_URL ist nicht gesetzt (persönlicher Link, 24 h gültig — "
                 "gehört NICHT ins Repo).")
    main(url, a.max_records, a.messen, a.teilgroesse)
