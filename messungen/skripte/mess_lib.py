"""Messbibliothek des Dataset-Hubs — Phase 1.

Regeln (Startauftrag, verbindlich):
- Nichts erfinden: jeder berichtete Wert stammt aus einer gespeicherten Antwort.
- Ausfälle vermerken, nie überbrücken: Netzfehler werden protokolliert und erscheinen
  im Ergebnis-JSON; sie sehen nie wie ein leeres Ergebnis aus.
- Nur lesende Abfragen dokumentierter API-Endpunkte, mit Drossel und klarem User-Agent.
"""
import datetime
import gzip
import json
import pathlib
import time
import urllib.error
import urllib.request

UA = "dataset-hub-messung/0.1 (https://github.com/frankbueltge/dataset-hub; f.bueltge@gmail.com)"
BASIS = pathlib.Path(__file__).resolve().parent.parent
ROHDATEN = BASIS / "rohdaten"
ERGEBNISSE = BASIS / "ergebnisse"


def jetzt() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def heute() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def hole(url: str, timeout: int = 60, versuche: int = 3, pause: float = 2.0,
         accept: str = "application/json"):
    """GET mit User-Agent und Wiederholung.

    Ein HTTP-Fehlerstatus ist ein Messergebnis und wird zurückgegeben (bei 429/502/503
    mit Backoff erneut versucht). Ein Netzausfall nach allen Versuchen wirft
    RuntimeError — der Aufrufer protokolliert ihn als Ausfall.
    """
    letzter = None
    for i in range(versuche):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read(), {k.lower(): v for k, v in r.headers.items()}
        except urllib.error.HTTPError as e:
            body = e.read()
            if e.code in (429, 502, 503) and i < versuche - 1:
                time.sleep(pause * (i + 1) * 2)
                continue
            return e.code, body, {k.lower(): v for k, v in e.headers.items()}
        except Exception as e:  # Timeout, DNS, Verbindungsabbruch
            letzter = e
            time.sleep(pause * (i + 1))
    raise RuntimeError(f"AUSFALL nach {versuche} Versuchen: {url} — {letzter}")


class Messung:
    """Sammelt Abfragen, Ausfälle und Ergebnisse einer Quelle; schreibt das Ergebnis-JSON."""

    def __init__(self, quelle: str):
        self.b = {"quelle": quelle, "beginn": jetzt(), "abfragen": [], "ausfaelle": []}

    def frag(self, zweck: str, url: str, **kw):
        eintrag = {"zweck": zweck, "url": url}
        self.b["abfragen"].append(eintrag)
        try:
            status, body, header = hole(url, **kw)
        except RuntimeError as e:
            eintrag["ausfall"] = str(e)
            self.b["ausfaelle"].append({"zweck": zweck, "url": url, "fehler": str(e)})
            return None, None, None
        eintrag["http_status"] = status
        return status, body, header

    def roh(self, name: str, daten: bytes) -> str:
        ROHDATEN.mkdir(exist_ok=True)
        pfad = ROHDATEN / name
        pfad.write_bytes(gzip.compress(daten))
        return str(pfad.relative_to(BASIS))

    def schreibe(self):
        ERGEBNISSE.mkdir(exist_ok=True)
        self.b["ende"] = jetzt()
        pfad = ERGEBNISSE / f"{heute()}-{self.b['quelle']}.json"
        pfad.write_text(json.dumps(self.b, indent=2, ensure_ascii=False) + "\n")
        print(f"geschrieben: {pfad}")
        if self.b["ausfaelle"]:
            print(f"ACHTUNG: {len(self.b['ausfaelle'])} Ausfälle protokolliert")


def abdeckung(records, felder):
    """Anteil der Records, in denen ein Feld belegt ist.

    Extraktionsfehler zählen als 'nicht belegt' — nie als Treffer.
    """
    n = len(records)
    aus = {"n": n, "felder": {}}
    for name, f in felder.items():
        k = 0
        for r in records:
            try:
                if f(r):
                    k += 1
            except Exception:
                pass
        aus["felder"][name] = {"anzahl": k, "anteil": round(k / n, 3) if n else None}
    return aus


def histogramm(records, f, maxi: int = 15):
    """Werteverteilung eines Feldes über die Stichprobe (defensiv, gekappt)."""
    zaehl = {}
    for r in records:
        try:
            w = f(r)
        except Exception:
            w = None
        w = str(w) if w is not None else "(leer)"
        zaehl[w] = zaehl.get(w, 0) + 1
    top = dict(sorted(zaehl.items(), key=lambda kv: -kv[1])[:maxi])
    if len(zaehl) > maxi:
        top["(weitere)"] = sum(zaehl.values()) - sum(top.values())
    return top
