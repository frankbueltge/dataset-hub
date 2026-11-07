#!/usr/bin/env python3
"""Ruft die Zugriffswege der Urteilsvorlage ab und legt die Antworten als Beleg ab.

Warum es dieses Skript gibt (2026-11-07): Die Urteilsroutine hat die Zugriffswege bis
dahin selbst per `curl` geprüft, meist in Shell-Schleifen mit Variablen und Pipes in
`python3`. Solche Befehle lässt die Befehlsausführung einer unbeaufsichtigten Sitzung
immer von einem Menschen freigeben, und das täglich bis zu zehnmal. Der Abruf ist
außerdem rein deterministisch und gehört nach der Bauregel ohnehin nicht ins Urteil,
sondern in die Pipeline. Das Urteil liest danach nur noch `urteil/belege.jsonl`.

Je Zugriffsweg festgehalten: HTTP-Status, finale URL nach Weiterleitungen,
Inhaltstyp, Größe, der Seitentitel (<title>, og:title oder JSON-Feld `title`/`name`)
und ob der registrierte Titel im abgerufenen Text vorkommt. Für zwei Quellen, deren
Webseiten den Inhalt erst per JavaScript nachladen, wird zusätzlich die dokumentierte
öffentliche API desselben Objekts gefragt (GBIF, ArcGIS-REST mit `f=json`); das steht
als `abgeleitet: true` am Beleg, damit niemand es für den Zugriffsweg selbst hält.

Ausfälle werden vermerkt, nie überbrückt: Ein Netzausfall ist `status: null` mit
Fehlertext, kein „nicht erreichbar".

Aufrufe:
    python3 pipeline/belege.py                      # alle URLs aus urteil/*.jsonl
    python3 pipeline/belege.py --url https://…      # eine zusätzliche URL, wörtlich
    python3 pipeline/belege.py --url https://… --suche "Crotalaria pallida"
"""
import argparse
import html
import json
import re
import sys
import time
from urllib.parse import urlparse, urlsplit, urlunsplit

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from hub_lib import WURZEL, hole, jetzt, jsonl_lesen  # noqa: E402

URTEIL = WURZEL / "urteil"
MAX_TEXT = 2_000_000  # mehr Text braucht der Titelabgleich nicht
DROSSEL_JE_HOST = 1.0

_GBIF_DATASET = re.compile(r"^https?://(www\.)?gbif\.org/dataset/([0-9a-f-]{36})/?$", re.I)
_GBIF_DOWNLOAD = re.compile(r"^https?://(www\.)?gbif\.org/occurrence/download/([0-9]+-[0-9]+)/?$", re.I)
_ARCGIS_REST = re.compile(r"/arcgis/rest/services/.+/(FeatureServer|MapServer)(/\d+)?/?$", re.I)


def normalisiere(text: str) -> str:
    import unicodedata
    t = unicodedata.normalize("NFKD", text or "").lower()
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", t)).strip()


def seitentitel(text: str, inhaltstyp: str) -> str | None:
    if "json" in (inhaltstyp or ""):
        try:
            d = json.loads(text)
        except ValueError:
            return None
        if isinstance(d, dict):
            for k in ("title", "name", "titel"):
                if isinstance(d.get(k), str) and d[k].strip():
                    return d[k].strip()
        return None
    for muster in (r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)',
                   r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title',
                   r"<title[^>]*>(.*?)</title>"):
        m = re.search(muster, text, re.I | re.S)
        if m and m.group(1).strip():
            return re.sub(r"\s+", " ", html.unescape(m.group(1))).strip()
    return None


def kommt_vor(suche: str | None, text: str) -> bool | None:
    n = normalisiere(suche or "")
    if len(n) < 3:
        return None
    return n in normalisiere(text)


def abgeleitete_api(url: str) -> str | None:
    """Die öffentliche API desselben Objekts, wo die Webseite den Inhalt nachlädt."""
    m = _GBIF_DATASET.match(url or "")
    if m:
        return f"https://api.gbif.org/v1/dataset/{m.group(2)}"
    m = _GBIF_DOWNLOAD.match(url or "")
    if m:
        return f"https://api.gbif.org/v1/occurrence/download/{m.group(2)}"
    teile = urlsplit(url or "")
    if _ARCGIS_REST.search(teile.path) and "f=" not in teile.query:
        query = (teile.query + "&" if teile.query else "") + "f=json"
        return urlunsplit((teile.scheme, teile.netloc, teile.path, query, ""))
    return None


def sammle(kandidaten: list, stichprobe: list) -> list:
    """(eintrag_id, registrierter_titel, url) in fester Reihenfolge, ohne Doppelte."""
    gesehen, aufgaben = set(), []

    def neu(e):
        url = (e.get("url") or "").strip()
        if url and (e.get("id"), url) not in gesehen:
            gesehen.add((e.get("id"), url))
            aufgaben.append({"id": e.get("id"), "titel": e.get("titel"), "url": url})

    for k in kandidaten:
        for e in k.get("eintraege") or []:
            neu(e)
    for e in stichprobe:
        neu(e)
    return aufgaben


class Abrufer:
    def __init__(self, drossel=DROSSEL_JE_HOST, holen=hole):
        self.drossel, self.holen, self.naechster = drossel, holen, {}

    def __call__(self, url: str, suche: str | None, abgeleitet=False) -> dict:
        host = urlparse(url).netloc.lower()
        rest = self.naechster.get(host, 0) - time.monotonic()
        if rest > 0:
            time.sleep(rest)
        self.naechster[host] = time.monotonic() + self.drossel
        beleg = {"url": url, "abgerufen": jetzt()}
        if abgeleitet:
            beleg["abgeleitet"] = True
        try:
            status, body, kopf, finale = self.holen(url, timeout=30, versuche=2, accept="*/*")
        except RuntimeError as e:
            beleg.update(status=None, ausfall=str(e))
            return beleg
        typ = kopf.get("content-type", "")
        text = body[:MAX_TEXT].decode("utf-8", "replace") if (
            "text" in typ or "json" in typ or "xml" in typ or not typ) else ""
        beleg.update(status=status, finale_url=finale, inhaltstyp=typ, bytes=len(body),
                     seitentitel=seitentitel(text, typ) if text else None,
                     titel_im_text=kommt_vor(suche, text) if text else None)
        return beleg


def pruefe(aufgaben: list, abrufer) -> list:
    belege = []
    for a in aufgaben:
        b = {"id": a["id"], "registrierter_titel": a["titel"], **abrufer(a["url"], a["titel"])}
        api = abgeleitete_api(a["url"])
        if api:
            b["api"] = abrufer(api, a["titel"], abgeleitet=True)
        belege.append(b)
    return belege


def zeile(b: dict) -> str:
    def kurz(x):
        if x.get("status") is None:
            return f"AUSFALL ({x.get('ausfall', '')[:60]})"
        treffer = {True: "Titel gefunden", False: "Titel NICHT im Text", None: "kein Text"}
        return (f"{x['status']} · {x.get('inhaltstyp', '')[:30]} · "
                f"{treffer[x.get('titel_im_text')]} · Seitentitel: {x.get('seitentitel')!r}")
    s = f"{b.get('id') or '-'}  {b['url']}\n    {kurz(b)}"
    if b.get("finale_url") and b["finale_url"] != b["url"]:
        s += f"\n    → {b['finale_url']}"
    if b.get("api"):
        s += f"\n    API {b['api']['url']}: {kurz(b['api'])}"
    return s


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--url", help="eine zusätzliche URL wörtlich prüfen statt der Vorlage")
    p.add_argument("--suche", help="Text, der auf der Seite vorkommen soll (mit --url)")
    a = p.parse_args(argv)
    abrufer = Abrufer()
    if a.url:
        b = {"id": None, "registrierter_titel": a.suche, **abrufer(a.url, a.suche)}
        api = abgeleitete_api(a.url)
        if api:
            b["api"] = abrufer(api, a.suche, abgeleitet=True)
        with (URTEIL / "belege.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(b, ensure_ascii=False) + "\n")
        print(zeile(b))
        return
    aufgaben = sammle(jsonl_lesen(URTEIL / "kandidaten.jsonl"),
                      jsonl_lesen(URTEIL / "stichprobe.jsonl"))
    belege = pruefe(aufgaben, abrufer)
    (URTEIL / "belege.jsonl").write_text(
        "".join(json.dumps(b, ensure_ascii=False) + "\n" for b in belege), encoding="utf-8")
    print(f"Belege: {len(belege)} Zugriffswege abgerufen → urteil/belege.jsonl")
    for b in belege:
        print(zeile(b))


if __name__ == "__main__":
    main()
