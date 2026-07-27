#!/usr/bin/env python3
"""Erzeugt die statischen Daten der Oberfläche aus dem Bestand.

Die Oberfläche folgt den Daten: sie zeigt, was aufgenommen wurde — samt Lücken und
Prüfstand. Sie bestimmt nichts. Einzige Quelle ist bestand/hub.sqlite (derselbe
Bestand, den die Pipelines als Snapshot laden).
"""
import gzip
import json
import pathlib
import sqlite3
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "pipeline"))
from hub_lib import BESTAND, jetzt  # noqa: E402

ZIEL = pathlib.Path(__file__).resolve().parent / "public" / "daten"


def main():
    ZIEL.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(BESTAND / "hub.sqlite")
    db.row_factory = sqlite3.Row

    # Zwei Dateien mit verschiedenem Zweck:
    #   eintraege.json — schlank, geht an den Browser (Suche/Filter über den ganzen Bestand)
    #   details.json   — reich, wird NUR beim Bauen gelesen (Einzelseiten, JSON-LD) und
    #                    erreicht den Browser nie. Beschreibung und Urheber gehören dort
    #                    hinein: schema.org/Dataset wertet sie aus, aber sie würden den
    #                    Client-Download vervielfachen.
    # Beschreibungen sind, anders als Titel und Kennungen, schutzfähige Texte ihrer
    # Verfasser. Im Wortlaut veröffentlicht werden sie nur, wo die Quelle das
    # ausdrücklich erlaubt — bei DataCite per CC0-Verzicht (messungen/register.md,
    # Gate G5). Für HuggingFace ist die Reichweite der Erlaubnis außerhalb der
    # Plattform offen, für ArcGIS-Einträge mit `custom`-Lizenz ebenfalls; von dort
    # wird der Wortlaut zurückgehalten, bis das geklärt ist.
    BESCHREIBUNG_FREIGEGEBEN = {"datacite"}
    quelle_je_id = {i: q for i, q in db.execute("SELECT id, quelle FROM eintraege")}

    # Seit der Neufassung des Registerzwecks (frankbueltge.de →
    # docs/design/2026-07-27-register-neufassung.md, §4) zeigt die Oberfläche nur den
    # KERNBESTAND: Suche, Listen, Unterseiten, Sitemap und JSON-LD. Der übrige Bestand
    # verschwindet nicht — er bleibt über den Snapshot abfragbar, den die Praxen laden.
    # Die Zähler unten weisen beide Größen aus, damit die Oberfläche sagen kann, wovon
    # sie einen Ausschnitt zeigt.
    NUR_KERNBESTAND = "WHERE kernbestand = 1"

    # ---- Fassungen und Beziehungen: der Eigenwert, den die Quellseite nicht zeigt ----
    # Ein DataCite-Datensatzblatt zeigt genau einen Datensatz. Das Register weiß mehr:
    # welche anderen Fassungen zu demselben Werk gehören (Dedup R1–R4) und welche
    # geernteten Beziehungen auf Einträge zeigen, die es selbst führt. Gemessen am
    # 27.07.: 14.073 von 16.494 Kernbestand-Einträgen liegen in einem Werk mit mehreren
    # Fassungen, und 13.100 der 40.380 Beziehungen (32,4 %) haben ein Ziel im eigenen
    # Bestand. Beides lag bisher in der Datenbank und auf keiner Seite.
    # Geschwister werden über den GANZEN Bestand gesammelt, nicht nur über den
    # Kernbestand: eine Fassung, die das Relevanzkriterium nicht trifft, existiert
    # trotzdem, und sie zu verschweigen hieße, das Werk unvollständig darzustellen.
    # Das Merkmal `s` (Seite) sagt, ob es dafür eine Unterseite gibt — nur dann darf
    # die Vorlage verlinken, sonst zeigt sie den Eintrag ohne Verweis.
    geschwister, werk_je_id = {}, {}
    for r in db.execute("SELECT id, werk_id, titel, publikationsjahr, quelle, kernbestand "
                        "FROM eintraege"):
        werk_je_id[r["id"]] = r["werk_id"]
        geschwister.setdefault(r["werk_id"], []).append(
            {"i": r["id"], "t": r["titel"], "j": r["publikationsjahr"], "q": r["quelle"],
             "s": bool(r["kernbestand"])})

    # DOI → eigener Eintrag, damit eine Beziehung als interner Verweis erkennbar wird.
    eintrag_je_doi = {}
    for r in db.execute(f"SELECT id, json FROM eintraege {NUR_KERNBESTAND}"):
        for ident in json.loads(r["json"]).get("identifikatoren") or []:
            if ident.get("schema") == "doi" and ident.get("wert"):
                eintrag_je_doi[ident["wert"].lower()] = r["id"]

    # Ein Eintrag führt bis zu 499 Beziehungen (Mittel 2,5; 264 Einträge über 20).
    # Alle auszugeben blähte details.json auf, ohne dass eine Seite 499 Verweise
    # sinnvoll zeigt. Gekappt wird deshalb — aber sichtbar: die Seite nennt die
    # Gesamtzahl, nicht nur die gezeigten.
    BEZIEHUNGS_KAPPUNG = 20
    beziehungen = {}
    for r in db.execute("SELECT von_id, typ, ziel_schema, ziel FROM relationen"):
        ziel = (r["ziel"] or "").strip()
        intern = eintrag_je_doi.get(ziel.lower().replace("https://doi.org/", ""))
        b = {"typ": r["typ"], "ziel": ziel, "schema": r["ziel_schema"]}
        if intern:
            b["i"] = intern
        beziehungen.setdefault(r["von_id"], []).append(b)

    details = {}
    for r in db.execute(f"SELECT id, json FROM eintraege {NUR_KERNBESTAND} ORDER BY id"):
        e = json.loads(r["json"])
        d = {}
        if ((e.get("beschreibung") or "").strip()
                and quelle_je_id.get(r["id"]) in BESCHREIBUNG_FREIGEGEBEN):
            d["beschreibung"] = e["beschreibung"]
        if e.get("urheber"):
            d["urheber"] = e["urheber"]
        if (e.get("lizenz") or {}).get("roh"):
            d["lizenz_roh"] = e["lizenz"]["roh"]
        if e.get("raeumlichkeit"):
            d["raeumlichkeit"] = e["raeumlichkeit"]
        if e.get("daten"):
            d["daten"] = e["daten"]
        # Zugriffs-URL, Quell-ID und Werk-Zugehörigkeit werden NUR auf den Einzelseiten
        # gebraucht, nicht für Suche und Filter. Sie liegen deshalb hier statt im
        # Browser-Index: URLs sind lang, und der Index wächst mit jedem Eintrag mit.
        d["zugang_url"] = (e.get("zugang") or {}).get("url") or ""
        d["quell_id"] = (e.get("fundstellen") or [{}])[0].get("quell_id") or ""

        # Andere Fassungen desselben Werks — der Eintrag selbst ist nicht dabei.
        andere = [g for g in geschwister.get(werk_je_id.get(r["id"]), [])
                  if g["i"] != r["id"]]
        if andere:
            d["fassungen"] = sorted(andere, key=lambda g: (-(g["j"] or 0), g["t"]))

        alle_b = beziehungen.get(r["id"], [])
        if alle_b:
            # Interne Verweise zuerst: sie sind der Teil, den nur dieses Register hat.
            alle_b.sort(key=lambda b: (0 if "i" in b else 1, b["typ"]))
            d["beziehungen"] = alle_b[:BEZIEHUNGS_KAPPUNG]
            d["beziehungen_gesamt"] = len(alle_b)
        details[r["id"]] = d

    zeilen = []
    for r in db.execute(f"""
        SELECT id, werk_id, quelle, quell_id, granularitaet, titel, herausgeber,
               publikationsjahr, lizenz_id, zugang_url, zugang_geprueft,
               zugang_http_status, status, kernbestand_herkunft
        FROM eintraege {NUR_KERNBESTAND} ORDER BY id
    """):
        # Schlanker Suchindex: nur was Suche, Filter und Ergebnisliste brauchen.
        # url/quell_id/werk_id stehen in details.json (siehe oben) — sie würden den
        # Browser-Download um rund ein Drittel aufblähen, ohne dort gebraucht zu werden.
        zeilen.append({
            "i": r["id"], "q": r["quelle"],
            "g": r["granularitaet"], "t": r["titel"], "h": r["herausgeber"] or "",
            "j": r["publikationsjahr"], "l": r["lizenz_id"] or "",
            "v": r["zugang_geprueft"], "s": r["zugang_http_status"], "z": r["status"],
            # Herkunft des Kernbestand-Merkmals: "regel" (ein Begriff im Titel
            # entschied) oder "urteil" (die Urteilsroutine hat entschieden). Die
            # Einzelseite soll sagen können, WARUM ein Eintrag hier ist.
            "k": r["kernbestand_herkunft"],
        })

    meta = dict(db.execute("SELECT schluessel, wert FROM meta"))
    fassungen = {}
    for r in db.execute("SELECT werk_id, COUNT(*) n FROM eintraege GROUP BY werk_id HAVING n>1"):
        fassungen[r["werk_id"]] = r["n"]

    manifeste = []
    for m in sorted((pathlib.Path(__file__).resolve().parent.parent
                     / "fundstellen" / "manifeste").glob("*.json")):
        d = json.loads(m.read_text())
        manifeste.append({k: d.get(k) for k in
                          ("quelle", "seit", "bis", "records", "vollstaendig")})

    # Das Ablehnungsregister ist append-only: ein Eintrag, der beim ersten Bau an einer
    # Schranke scheiterte und später — etwa nach erfolgreicher HTTP-Auflösung — doch
    # aufgenommen wurde, behält sein Ablehnungs-EREIGNIS. Die Ereigniszahl ist deshalb
    # keine Aussage darüber, was aktuell draußen ist. Beides wird getrennt ausgewiesen,
    # statt die größere Zahl als „verworfen" zu zeigen.
    im_bestand = {(q, p) for q, p in db.execute("SELECT quelle, quell_id FROM eintraege")}
    aktuell = {}
    ereignisse_gesamt = 0
    for r in db.execute("SELECT quelle, quell_id, grund FROM ablehnungen"):
        ereignisse_gesamt += 1
        if (r["quelle"], r["quell_id"]) not in im_bestand:
            aktuell[r["grund"]] = aktuell.get(r["grund"], 0) + 1
    ablehnungen = sorted(({"grund": g, "n": n} for g, n in aktuell.items()),
                         key=lambda x: -x["n"])
    ablehnungen_meta = {
        "ereignisse_gesamt": ereignisse_gesamt,
        "aktuell_verworfen": sum(aktuell.values()),
        "spaeter_doch_aufgenommen": ereignisse_gesamt - sum(aktuell.values()),
    }
    ausfaelle = [dict(r) for r in db.execute(
        "SELECT datum, quelle, fehler, kontext FROM ausfaelle ORDER BY datum DESC LIMIT 50")]
    quellen = [dict(r) for r in db.execute(
        "SELECT quelle, COUNT(*) n FROM eintraege GROUP BY quelle ORDER BY n DESC")]
    db.close()

    (ZIEL / "eintraege.json").write_text(json.dumps(zeilen, ensure_ascii=False,
                                                    separators=(",", ":")))
    with gzip.open(ZIEL / "eintraege.json.gz", "wt", encoding="utf-8") as f:
        json.dump(zeilen, f, ensure_ascii=False, separators=(",", ":"))

    (ZIEL / "meta.json").write_text(json.dumps({
        "erzeugt": jetzt(),
        "schema_version": meta.get("schema_version"),
        "gebaut_am": meta.get("gebaut_am"),
        "zaehler": {k: int(meta.get(k, 0)) for k in
                    ("eintraege", "werke", "fundstellen", "abgelehnt_gesamt",
                     "aufgeloest_versucht", "aufgeloest_bestaetigt",
                     # Kernbestand = was diese Oberfläche zeigt; "eintraege" = der
                     # ganze Bestand, den der Snapshot trägt. Beide Zahlen stehen
                     # nebeneinander, damit die Seite den Ausschnitt benennen kann
                     # statt ihn als das Ganze auszugeben.
                     "kernbestand", "kernbestand_regel", "kernbestand_urteil",
                     "kernbestand_grenzfaelle_offen")},
        "mehrfassungs_werke": len(fassungen),
        "quellfenster": manifeste,
        "quellen": quellen,
        "ablehnungen": ablehnungen,
        "ablehnungen_meta": ablehnungen_meta,
        "ausfaelle": ausfaelle,
    }, ensure_ascii=False, indent=2))

    (ZIEL / "details.json").write_text(json.dumps(details, ensure_ascii=False,
                                                  separators=(",", ":")))

    print(f"{len(zeilen)} Kernbestand-Einträge von {meta.get('eintraege')} im Bestand "
          f"→ {ZIEL}")
    for name in ("eintraege.json", "eintraege.json.gz", "details.json"):
        print(f"  {name:<20} {(ZIEL / name).stat().st_size / 1e6:.2f} MB")
    mit_beschreibung = sum(1 for d in details.values() if d.get("beschreibung"))
    print(f"  details: {len(details)} Einträge, davon {mit_beschreibung} mit Beschreibung "
          f"(erreicht den Browser nicht)")


if __name__ == "__main__":
    main()
