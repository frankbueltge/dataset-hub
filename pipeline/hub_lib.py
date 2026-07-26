"""Gemeinsame Bausteine der Hub-Pipeline (Phase 2). Nur Standardbibliothek.

Regeln (Startauftrag, verbindlich): nichts erfinden; Ausfälle vermerken, nie
überbrücken; keine Modell-APIs; URLs wörtlich aus der Quelle (dokumentierte
Quellen-Ausnahmen: schema/SCHEMA.md).
"""
import datetime
import gzip
import hashlib
import json
import pathlib
import time
import urllib.error
import urllib.request

UA = "dataset-hub-pipeline/0.1 (https://github.com/frankbueltge/dataset-hub; f.bueltge@gmail.com)"
WURZEL = pathlib.Path(__file__).resolve().parent.parent
FUNDSTELLEN = WURZEL / "fundstellen"
MANIFESTE = FUNDSTELLEN / "manifeste"
REGISTER = WURZEL / "register"
JOURNAL = WURZEL / "journal"
PRUEFUNGEN = WURZEL / "pruefungen"
BESTAND = WURZEL / "bestand"
SNAPSHOTS = WURZEL / "snapshots"

SCHEMA_VERSION = "0.2.0"


def jetzt() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def heute() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def hole(url: str, timeout: int = 60, versuche: int = 3, pause: float = 2.0,
         accept: str = "application/json", methode: str = "GET", koerper_lesen: bool = True):
    """HTTP-Abruf mit Wiederholung. HTTP-Fehlerstatus ist ein Ergebnis; Netzausfall
    nach allen Versuchen wirft RuntimeError (Aufrufer protokolliert den Ausfall).
    Mit koerper_lesen=False wird nur Status/Header/finale URL geholt."""
    letzter = None
    for i in range(versuche):
        try:
            req = urllib.request.Request(url, method=methode,
                                         headers={"User-Agent": UA, "Accept": accept})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read() if koerper_lesen else b""
                return r.status, body, {k.lower(): v for k, v in r.headers.items()}, r.geturl()
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503) and i < versuche - 1:
                time.sleep(pause * (i + 1) * 2)
                continue
            return e.code, e.read() if koerper_lesen else b"", \
                {k.lower(): v for k, v in e.headers.items()}, e.url
        except Exception as e:
            letzter = e
            time.sleep(pause * (i + 1))
    raise RuntimeError(f"AUSFALL nach {versuche} Versuchen: {url} — {letzter}")


def sha256_datei(pfad: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(pfad, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def jsonl_anhaengen(pfad: pathlib.Path, obj: dict):
    pfad.parent.mkdir(parents=True, exist_ok=True)
    with open(pfad, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def jsonl_lesen(pfad: pathlib.Path):
    if not pfad.exists():
        return []
    aus = []
    with open(pfad, encoding="utf-8") as f:
        for zeile in f:
            zeile = zeile.strip()
            if zeile:
                aus.append(json.loads(zeile))
    return aus


def jsonl_gz_lesen(pfad: pathlib.Path):
    with gzip.open(pfad, "rt", encoding="utf-8") as f:
        for zeile in f:
            zeile = zeile.strip()
            if zeile:
                yield json.loads(zeile)


def vermerk_ausfall(quelle: str, lauf: str, fehler, kontext: str = ""):
    jsonl_anhaengen(REGISTER / "ausfaelle.jsonl",
                    {"datum": jetzt(), "quelle": quelle, "lauf": lauf,
                     "fehler": str(fehler)[:500], "kontext": kontext})


def normalisiere_doi(wert: str) -> str:
    w = (wert or "").strip().lower()
    for praefix in ("https://doi.org/", "http://doi.org/",
                    "https://dx.doi.org/", "http://dx.doi.org/", "doi:"):
        if w.startswith(praefix):
            w = w[len(praefix):]
    return w


def hub_id(pid_schema: str, pid_wert: str) -> str:
    return "dh-" + hashlib.sha256(f"{pid_schema}:{pid_wert}".encode()).hexdigest()[:16]
