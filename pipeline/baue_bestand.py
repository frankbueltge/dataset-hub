#!/usr/bin/env python3
"""Bestandsbau: Fundstellen + Journal + Auflösungen → bestand/hub.sqlite.

Deterministisch: gleiche Eingaben ergeben denselben Bestand (bis auf den
Bau-Zeitstempel). Abgelehnte Fundstellen wandern mit Grundcode ins
Ablehnungsregister (nur neue — keine Dubletten im Register).
"""
import json
import sqlite3

from hub_lib import (BESTAND, FUNDSTELLEN, JOURNAL, PRUEFUNGEN, REGISTER,
                     SCHEMA_VERSION, jetzt, jsonl_anhaengen, jsonl_gz_lesen, jsonl_lesen)
from normalisiere import NORMALISIERER
from schranken import pruefe
from dedupe import leite_gruppen_ab


def lade_fundstellen():
    """Jüngste Fundstelle je (quelle, quell_id); Reihenfolge deterministisch."""
    juengste = {}
    alle = []
    for datei in sorted(FUNDSTELLEN.glob("*.jsonl.gz")):
        for fund in jsonl_gz_lesen(datei):
            schluessel = (fund.get("quelle"), fund.get("quell_id"))
            alle.append({k: fund.get(k) for k in ("quelle", "quell_id", "geerntet")})
            alt = juengste.get(schluessel)
            if not alt or fund.get("geerntet", "") > alt.get("geerntet", ""):
                juengste[schluessel] = fund
    return juengste, alle


def main():
    BESTAND.mkdir(exist_ok=True)
    fundstellen, alle_fundstellen = lade_fundstellen()

    # Auflösungen VORAB laden und VOR der Schranken-Prüfung anheften: mindestens
    # eine Quelle (HuggingFace, konstruierte Zugriffs-URL) macht die Aufnahme von
    # einer bereits bestätigten Auflösung abhängig (schranken.py:
    # 'konstruierte-url-ungeprueft'). Ohne diese Reihenfolge sähe schranken.pruefe()
    # immer nur den Anfangszustand 'geprueft: none'.
    aufloesungen = {}
    for z in jsonl_lesen(PRUEFUNGEN / "aufloesungen.jsonl"):
        aufloesungen[z["id"]] = z

    # Normalisieren + Schranken
    eintraege, abgelehnt = {}, []
    for schluessel in sorted(fundstellen):
        fund = fundstellen[schluessel]
        normalisierer = NORMALISIERER.get(fund.get("quelle"))
        if not normalisierer:
            abgelehnt.append((fund, "keine-normalisierung-fuer-quelle"))
            continue
        e = normalisierer(fund)
        a = aufloesungen.get(e["id"])
        if a:
            # 'versucht' unterscheidet "geprüft, Host antwortete nicht mit 2xx" von
            # "nie geprüft" — ein 403 (Bot-Schutz) ist kein toter Link und kein Nicht-Versuch.
            e["zugang"].update({
                "geprueft": "landing" if a.get("ok") else "versucht",
                "geprueft_am": a.get("datum", ""),
                "http_status": a.get("http_status"),
                "finale_url": a.get("finale_url", "") if a.get("ok") else "",
            })
        grund = pruefe(e)
        if grund:
            abgelehnt.append((fund, grund))
            continue
        alt = eintraege.get(e["id"])
        if alt:
            # gleiche PID aus mehreren Fundstellen (R1): Herkunft zusammenführen
            alt["fundstellen"].extend(e["fundstellen"])
        else:
            eintraege[e["id"]] = e

    # Ablehnungsregister: nur neue Einträge anhängen
    register_pfad = REGISTER / "ablehnungen.jsonl"
    bekannt = {(z.get("quelle"), z.get("quell_id"), z.get("grund"))
               for z in jsonl_lesen(register_pfad)}
    neu_abgelehnt = 0
    for fund, grund in abgelehnt:
        schluessel = (fund.get("quelle"), fund.get("quell_id"), grund)
        if schluessel not in bekannt:
            jsonl_anhaengen(register_pfad, {"datum": jetzt(), "quelle": fund.get("quelle"),
                                            "quell_id": fund.get("quell_id"), "grund": grund})
            bekannt.add(schluessel)
            neu_abgelehnt += 1

    # Auflösungen sind bereits oben (vor der Schranken-Prüfung) an die Einträge
    # geheftet worden; hier nur noch für die Dedup-Stufe R3 (identische finale URL)
    # weiterreichen.

    # Dedup R1–R4 + Journal
    journal = jsonl_lesen(JOURNAL / "entscheidungen.jsonl")
    fassung_von, werk_von = leite_gruppen_ab(eintraege, aufloesungen, journal)

    # SQLite schreiben
    db_pfad = BESTAND / "hub.sqlite"
    if db_pfad.exists():
        db_pfad.unlink()
    db = sqlite3.connect(db_pfad)
    db.executescript("""
        CREATE TABLE meta (schluessel TEXT PRIMARY KEY, wert TEXT);
        CREATE TABLE eintraege (
            id TEXT PRIMARY KEY, werk_id TEXT, fassung_id TEXT,
            quelle TEXT, quell_id TEXT, granularitaet TEXT,
            titel TEXT, herausgeber TEXT, publikationsjahr INTEGER,
            lizenz_id TEXT, zugang_url TEXT, zugang_stufe TEXT,
            zugang_geprueft TEXT, zugang_http_status INTEGER,
            status TEXT, json TEXT
        );
        CREATE INDEX idx_werk ON eintraege(werk_id);
        CREATE INDEX idx_jahr ON eintraege(publikationsjahr);
        CREATE INDEX idx_lizenz ON eintraege(lizenz_id);
        CREATE TABLE relationen (von_id TEXT, typ TEXT, ziel_schema TEXT, ziel TEXT);
        CREATE TABLE fundstellen (quelle TEXT, quell_id TEXT, geerntet TEXT);
        CREATE TABLE ablehnungen (datum TEXT, quelle TEXT, quell_id TEXT, grund TEXT);
        CREATE TABLE ausfaelle (datum TEXT, quelle TEXT, lauf TEXT, fehler TEXT, kontext TEXT);
        CREATE VIRTUAL TABLE eintraege_fts USING fts5(id UNINDEXED, titel, beschreibung);
    """)
    for eid in sorted(eintraege):
        e = eintraege[eid]
        f0 = e["fundstellen"][0]
        db.execute("INSERT INTO eintraege VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            eid, werk_von[eid], fassung_von[eid], f0["quelle"], f0["quell_id"],
            e["granularitaet"], e["titel"], e["herausgeber"], e["publikationsjahr"],
            e["lizenz"]["id"], e["zugang"]["url"], e["zugang"]["stufe"],
            e["zugang"]["geprueft"], e["zugang"]["http_status"], e["status"],
            json.dumps(e, ensure_ascii=False)))
        db.execute("INSERT INTO eintraege_fts VALUES (?,?,?)",
                   (eid, e["titel"], e["beschreibung"]))
        for rel in e["relationen"]:
            db.execute("INSERT INTO relationen VALUES (?,?,?,?)",
                       (eid, rel["typ"], rel["ziel_schema"], rel["ziel"]))
    for f in alle_fundstellen:
        db.execute("INSERT INTO fundstellen VALUES (?,?,?)",
                   (f["quelle"], f["quell_id"], f["geerntet"]))
    for z in jsonl_lesen(REGISTER / "ablehnungen.jsonl"):
        db.execute("INSERT INTO ablehnungen VALUES (?,?,?,?)",
                   (z.get("datum"), z.get("quelle"), z.get("quell_id"), z.get("grund")))
    for z in jsonl_lesen(REGISTER / "ausfaelle.jsonl"):
        db.execute("INSERT INTO ausfaelle VALUES (?,?,?,?,?)",
                   (z.get("datum"), z.get("quelle"), z.get("lauf"),
                    z.get("fehler"), z.get("kontext")))

    werke = len(set(werk_von.values()))
    for k, v in (("schema_version", SCHEMA_VERSION), ("gebaut_am", jetzt()),
                 ("eintraege", len(eintraege)), ("werke", werke),
                 ("fundstellen", len(alle_fundstellen)),
                 ("abgelehnt_gesamt", len(abgelehnt)),
                 ("abgelehnt_neu", neu_abgelehnt),
                 ("aufgeloest_versucht", sum(1 for e in eintraege.values()
                                             if e["zugang"]["geprueft"] != "none")),
                 ("aufgeloest_bestaetigt", sum(1 for e in eintraege.values()
                                               if e["zugang"]["geprueft"] in ("landing", "download")))):
        db.execute("INSERT INTO meta VALUES (?,?)", (k, str(v)))
    db.commit()
    db.close()

    print(f"Bestand gebaut: {len(eintraege)} Einträge, {werke} Werke, "
          f"{len(alle_fundstellen)} Fundstellen, {len(abgelehnt)} abgelehnt "
          f"({neu_abgelehnt} neu im Register) → {db_pfad}")


if __name__ == "__main__":
    main()
