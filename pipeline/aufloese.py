#!/usr/bin/env python3
"""Auflösungs-Budget: prüft Zugriffswege per HTTP (Design §2.2).

Liest Fundstellen, normalisiert, wählt bis zu --budget ungeprüfte Einträge und löst
deren Zugriffs-URL tatsächlich auf. Ergebnisse landen append-only in
pruefungen/aufloesungen.jsonl. Ein Eintrag behauptet nie mehr, als hier geprüft wurde.

## Drossel je Host, nicht global (2026-07-27)

Die Zugriffswege zeigen NICHT auf DataCite, sondern auf die Landingpages der
Original-Repositorien — und sie sind extrem ungleich verteilt. Gemessen am
Kernbestand vom 27.07.: 16.494 Wege auf 205 Hosts, davon

    44,2 %  zenodo.org
    14,7 %  figshare.com
    11,7 %  data.mendeley.com
    ------  Top 10 = 89,2 %

Eine globale Drossel (bis 27.07.: 0,3 s zwischen allen Anfragen) hätte daraus bis zu
3 Anfragen je Sekunde gegen zenodo.org gemacht — das Dreifache dessen, was Zenodo
nicht angemeldeten Zugriffen zugesteht (60/min). Die Drossel gilt deshalb JE HOST,
und die Kandidaten werden reihum über die Hosts abgearbeitet statt der Reihe nach:
ein kleines Budget verteilt sich damit über viele Hosts, statt einen zu belasten.

Dazu drei Höflichkeiten, die vorher fehlten:
- `robots.txt` wird je Host einmal geholt und beachtet;
- ein 429 oder 503 legt den Host für den Rest des Laufs still (kein Nachbohren);
- der User-Agent nennt Projekt und Kontakt (hub_lib.UA).
"""
import argparse
import collections
import sqlite3
import time
import urllib.robotparser
from urllib.parse import urlparse

from hub_lib import (BESTAND, FUNDSTELLEN, PRUEFUNGEN, UA, hole, jetzt,
                     jsonl_anhaengen, jsonl_gz_lesen, jsonl_lesen)
from normalisiere import NORMALISIERER

# Sekunden zwischen zwei Anfragen an DENSELBEN Host. 2,0 s = 30/min, die Hälfte
# dessen, was Zenodo nicht angemeldeten Zugriffen zugesteht.
DROSSEL_JE_HOST = 2.0

# Stati, bei denen ein Host für den Rest des Laufs in Ruhe gelassen wird.
RUECKZUG_STATI = {429, 503}

# Nur diese Stati gelten als BESTÄTIGT — der Server hat den Inhalt geliefert.
#
# 202 ist ausdrücklich NICHT dabei, obwohl es ein 2xx ist. Gemessen am 27.07.:
# 44 von 175 Prüfungen kamen mit 202 zurück, praktisch alle aus der
# figshare-Familie, deren CDN HEAD-Anfragen so beantwortet. „Accepted" heißt
# „angenommen, wird bearbeitet", nicht „hier ist die Ressource" — als
# „Zugriff bestätigt" auf einer Seite wäre das eine Behauptung ohne Deckung.
# Ein 202 löst deshalb den GET-Nachgang aus wie jeder andere Nicht-200.
BESTAETIGENDE_STATI = {200, 203, 206}


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


def kernbestand_ids():
    """Ids des Kernbestands aus dem gebauten Bestand — sie haben eine Seite und
    tragen die Behauptung „geprüft statt behauptet". Fehlt der Bestand, gibt es
    keine Vorauswahl (und der Aufrufer erfährt es)."""
    db_pfad = BESTAND / "hub.sqlite"
    if not db_pfad.exists():
        return None
    db = sqlite3.connect(db_pfad)
    ids = {i for (i,) in db.execute("SELECT id FROM eintraege WHERE kernbestand = 1")}
    db.close()
    return ids


class Hoeflichkeit:
    """Hält je Host fest, wann wieder angefragt werden darf, was robots.txt sagt
    und ob der Host sich zurückgemeldet hat („bitte nicht mehr")."""

    def __init__(self, drossel_je_host: float, robots_beachten: bool = True):
        self.drossel = drossel_je_host
        self.robots_beachten = robots_beachten
        self.naechster_erlaubt = collections.defaultdict(float)
        self.stillgelegt = {}
        self._robots = {}

    def darf(self, url: str) -> bool:
        if not self.robots_beachten:
            return True
        host = urlparse(url).netloc.lower()
        if host not in self._robots:
            rp = urllib.robotparser.RobotFileParser()
            wurzel = f"{urlparse(url).scheme}://{host}"
            try:
                status, body, _, _ = hole(f"{wurzel}/robots.txt", timeout=15, versuche=1,
                                          accept="text/plain")
                # Kein robots.txt (404) heißt: alles erlaubt. Ein Serverfehler heißt
                # NICHT „verboten" — dann wird wie ohne robots.txt verfahren, aber
                # die Drossel gilt weiterhin.
                rp.parse(body.decode("utf-8", "replace").splitlines()
                         if 200 <= status < 300 else [])
            except RuntimeError:
                rp.parse([])
            self._robots[host] = rp
        try:
            return self._robots[host].can_fetch(UA, url)
        except Exception:
            return True

    def warte(self, host: str):
        rest = self.naechster_erlaubt[host] - time.monotonic()
        if rest > 0:
            time.sleep(rest)
        self.naechster_erlaubt[host] = time.monotonic() + self.drossel

    def zurueckziehen(self, host: str, grund: str):
        self.stillgelegt[host] = grund


def loese_auf(url: str):
    """HEAD zuerst (billig), aber jedem Nicht-2xx wird mit GET nachgegangen.

    HEAD ist im Web unzuverlässig implementiert: Kaggle etwa antwortet auf HEAD mit
    404 und auf GET mit 200 (gemessen 2026-07-26 — 400 Einträge waren dadurch
    fälschlich als nicht erreichbar vermerkt). Ein HEAD-Fehlschlag ist deshalb kein
    Befund über die Ressource, sondern nur über die Methode; erst das GET zählt.

    Ausnahme seit 27.07.: Bei einem Rückzugs-Status (429/503) wird NICHT mit GET
    nachgesetzt — der Host hat gerade gesagt, dass er weniger will, nicht mehr.
    """
    status, _, _, finale = hole(url, timeout=20, versuche=1, accept="*/*",
                                methode="HEAD", koerper_lesen=False)
    if status in RUECKZUG_STATI:
        return status, finale
    if status not in BESTAETIGENDE_STATI:
        status, _, _, finale = hole(url, timeout=25, versuche=1, accept="*/*",
                                    koerper_lesen=False)
    return status, finale


def main(budget: int, drossel_je_host: float, wiederholen: bool = False,
         nur_kernbestand: bool = False, je_host: int = 0, robots: bool = True,
         erneut_status: set = None):
    pfad = PRUEFUNGEN / "aufloesungen.jsonl"
    letzte = {}
    for z in jsonl_lesen(pfad):
        letzte[z["id"]] = z
    # Positivauswahl statt Ausschluss: bei --erneut-status kommen NUR Einträge in
    # Frage, die diesen Status zuletzt gezeigt haben. Als Ausschlussliste gebaut
    # („alles, was nicht Status X hat, ist erledigt") fielen die nie geprüften
    # Einträge durch — sie stehen gar nicht im Protokoll und wären damit stillschweigend
    # in eine gezielte Nachprüfung geraten.
    nur_diese = None
    if erneut_status:
        # Nötig, wenn sich die AUSLEGUNG einer Antwort geändert hat, nicht die Antwort
        # selbst: Am 27.07. galt 202 erst als Bestätigung und dann nicht mehr. Das
        # Protokoll bleibt append-only — der alte Eintrag wird nicht angefasst,
        # sondern durch einen neuen abgelöst.
        nur_diese = {i for i, z in letzte.items()
                     if z.get("http_status") in erneut_status}
        schon = set()
    elif wiederholen:
        schon = {i for i, z in letzte.items() if z.get("ok")}
    else:
        schon = set(letzte)

    eintraege = lade_eintraege()
    erlaubte = None
    if nur_kernbestand:
        erlaubte = kernbestand_ids()
        if erlaubte is None:
            print("HINWEIS: kein gebauter Bestand — --nur-kernbestand wirkungslos.")

    kandidaten = [e for e in eintraege.values()
                  if e["id"] not in schon and e["zugang"]["url"]
                  and (erlaubte is None or e["id"] in erlaubte)
                  and (nur_diese is None or e["id"] in nur_diese)]
    kandidaten.sort(key=lambda e: e["fundstellen"][0].get("geerntet", ""), reverse=True)

    # Nach Host gruppieren und REIHUM abarbeiten: so verteilt sich ein kleines Budget
    # über viele Hosts, statt die 44 % von zenodo.org zuerst abzuräumen.
    je_host_warteschlange = collections.OrderedDict()
    for e in kandidaten:
        host = (urlparse(e["zugang"]["url"]).netloc or "").lower()
        if not host:
            continue
        je_host_warteschlange.setdefault(host, collections.deque()).append(e)
    if je_host:
        for host, warteschlange in je_host_warteschlange.items():
            while len(warteschlange) > je_host:
                warteschlange.pop()

    hoeflichkeit = Hoeflichkeit(drossel_je_host, robots_beachten=robots)
    ok = fehler = ausfaelle = uebersprungen_robots = 0
    geprueft = 0
    hosts_beruehrt = set()

    while geprueft < budget and je_host_warteschlange:
        for host in list(je_host_warteschlange):
            if geprueft >= budget:
                break
            if host in hoeflichkeit.stillgelegt:
                je_host_warteschlange.pop(host, None)
                continue
            warteschlange = je_host_warteschlange[host]
            if not warteschlange:
                je_host_warteschlange.pop(host, None)
                continue
            e = warteschlange.popleft()
            url = e["zugang"]["url"]

            if not hoeflichkeit.darf(url):
                # robots.txt verbietet — das ist ein Befund, kein Fehler, und wird
                # als solcher vermerkt statt still übersprungen.
                jsonl_anhaengen(pfad, {
                    "id": e["id"], "quelle": e["fundstellen"][0]["quelle"],
                    "quell_id": e["fundstellen"][0]["quell_id"], "url": url,
                    "datum": jetzt(), "ok": False, "robots_verbietet": True})
                uebersprungen_robots += 1
                continue

            hoeflichkeit.warte(host)
            hosts_beruehrt.add(host)
            eintrag = {"id": e["id"], "quelle": e["fundstellen"][0]["quelle"],
                       "quell_id": e["fundstellen"][0]["quell_id"],
                       "url": url, "datum": jetzt()}
            try:
                status, finale = loese_auf(url)
                eintrag.update({"http_status": status, "finale_url": finale,
                                "ok": status in BESTAETIGENDE_STATI})
                if status in RUECKZUG_STATI:
                    hoeflichkeit.zurueckziehen(host, f"HTTP {status}")
                    eintrag["host_stillgelegt"] = True
                ok += 1 if eintrag["ok"] else 0
                fehler += 0 if eintrag["ok"] else 1
            except RuntimeError as fehl:
                eintrag.update({"ausfall": str(fehl)[:300], "ok": False})
                ausfaelle += 1
            jsonl_anhaengen(pfad, eintrag)
            geprueft += 1

    print(f"aufgelöst: {geprueft} über {len(hosts_beruehrt)} Hosts "
          f"(ok {ok}, nicht-2xx {fehler}, Ausfälle {ausfaelle}, "
          f"durch robots.txt ausgelassen {uebersprungen_robots})")
    if hoeflichkeit.stillgelegt:
        print("stillgelegte Hosts (Rest des Laufs ausgesetzt):")
        for host, grund in hoeflichkeit.stillgelegt.items():
            print(f"  {host}: {grund}")
    offen = sum(len(w) for w in je_host_warteschlange.values())
    print(f"noch offen in dieser Auswahl: {offen}; bereits geprüft insgesamt: {len(schon)}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--budget", type=int, default=200)
    p.add_argument("--drossel-host", type=float, default=DROSSEL_JE_HOST,
                   help=f"Sekunden zwischen Anfragen an DENSELBEN Host (Standard {DROSSEL_JE_HOST})")
    p.add_argument("--je-host", type=int, default=0,
                   help="höchstens so viele Abrufe je Host in diesem Lauf (0 = unbegrenzt)")
    p.add_argument("--nur-kernbestand", action="store_true",
                   help="nur Einträge prüfen, die eine Seite haben")
    p.add_argument("--ohne-robots", action="store_true",
                   help="robots.txt NICHT abfragen (nur für Hosts ohne robots.txt sinnvoll)")
    p.add_argument("--wiederholen", action="store_true",
                   help="gescheiterte Prüfungen erneut versuchen (bestätigte bleiben)")
    p.add_argument("--erneut-status", type=int, nargs="+", default=None,
                   help="nur Einträge mit diesem zuletzt vermerkten HTTP-Status erneut "
                        "prüfen (z. B. 202, nachdem sich die Auslegung geändert hat)")
    a = p.parse_args()
    main(a.budget, a.drossel_host, a.wiederholen, a.nur_kernbestand,
         a.je_host, not a.ohne_robots,
         set(a.erneut_status) if a.erneut_status else None)
