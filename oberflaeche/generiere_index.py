#!/usr/bin/env python3
"""Erzeugt die statischen Daten der Oberfläche aus dem Bestand.

Die Oberfläche folgt den Daten: sie zeigt, was aufgenommen wurde — samt Lücken und
Prüfstand. Sie bestimmt nichts. Einzige Quelle ist bestand/hub.sqlite (derselbe
Bestand, den die Pipelines als Snapshot laden).
"""
import collections
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
    geschwister, werk_je_id, ist_kern = {}, {}, {}
    for r in db.execute("SELECT id, werk_id, titel, publikationsjahr, quelle, kernbestand "
                        "FROM eintraege"):
        werk_je_id[r["id"]] = r["werk_id"]
        ist_kern[r["id"]] = bool(r["kernbestand"])
        geschwister.setdefault(r["werk_id"], []).append(
            {"i": r["id"], "t": r["titel"], "j": r["publikationsjahr"], "q": r["quelle"],
             "s": bool(r["kernbestand"])})

    # Wer hat eine eigene Seite? Seit der Umstellung auf Werk-Seiten bekommt eine
    # Fassung eines Mehrfassungs-Werks KEINE eigene Seite mehr — das Werk trägt sie.
    # Anlass war nicht nur die Dublettenfrage: Fassungsseiten UND Werk-Seiten zusammen
    # ergaben 22.857 Dateien, und Cloudflare Pages nimmt 20.000 je Deployment. Die
    # Fassungsseiten waren ohnehin nicht kanonisch und nicht in der Sitemap.
    kern_je_werk = collections.Counter(w for i, w in werk_je_id.items() if ist_kern[i])

    def seite_von(eintrag_id):
        """Pfad der Seite, die diesen Eintrag zeigt — oder None. Nie anderswo bilden:
        ein Verweis auf eine nicht gebaute Fassungsseite wäre ein 404."""
        if not ist_kern.get(eintrag_id):
            return None
        werk = werk_je_id.get(eintrag_id)
        if kern_je_werk.get(werk, 0) > 1:
            return f"/datasets/work/{werk}"
        return f"/datasets/{eintrag_id}"

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
            # Der Pfad, nicht die Id: das Ziel kann eine Fassung ohne eigene Seite
            # sein, dann führt der Verweis auf deren Werk.
            ziel_seite = seite_von(intern)
            if ziel_seite:
                b["p"] = ziel_seite
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
        # Schlüssel `p` nur setzen, wenn es die Seite gibt — ein `null` im Export
        # wäre eine Adresse, die keine ist, und die Vorlage müsste raten.
        andere = []
        for g in geschwister.get(werk_je_id.get(r["id"]), []):
            if g["i"] == r["id"]:
                continue
            pfad = seite_von(g["i"])
            andere.append(dict(g, p=pfad) if pfad else dict(g))
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

    # ---- Werk-Ebene: eine Seite je Werk statt je Fassung ----
    # Gemessen am 27.07.: 16.494 Kernbestand-Einträge verteilen sich auf 8.579 Werke,
    # davon 5.127 mit genau zwei Fassungen. Das sind 10.254 paarweise fast identische
    # Seiten — gleicher Titel, gleicher Herausgeber, gleiches Jahr, oft dieselbe
    # Beschreibung. Die Werk-Seite fasst sie zusammen und zeigt stattdessen die
    # Fassungsgeschichte, die keine Quellseite so zeigt.
    #
    # Werke mit nur EINER Fassung bekommen bewusst keine Werk-Seite: sie wäre eine
    # Dublette der Eintragsseite und schüfe genau das Problem, das hier gelöst wird.
    werk_mitglieder = {}
    for r in db.execute(f"""
        SELECT id, werk_id, titel, herausgeber, publikationsjahr, lizenz_id, quelle,
               zugang_geprueft, zugang_http_status, zugang_url
        FROM eintraege {NUR_KERNBESTAND} ORDER BY id
    """):
        werk_mitglieder.setdefault(r["werk_id"], []).append(dict(r))

    werke = {}
    for werk_id, mitglieder in werk_mitglieder.items():
        if len(mitglieder) < 2:
            continue
        eigene = {m["id"] for m in mitglieder}
        # Vertreter: der Eintrag, auf den die Geschwister zeigen. Welche Fassung die
        # „aktuelle" ist, sagt das Register NICHT von sich aus — es liest ab, worauf
        # die Quelle selbst verweist. Nur wenn niemand zeigt, entscheidet das Jahr,
        # und dann heißt es „jüngster im Register", nicht „aktuelle Version".
        zeigt_auf = collections.Counter()
        for m in mitglieder:
            for b in beziehungen.get(m["id"], []):
                if b.get("i") in eigene and b["i"] != m["id"] and b["typ"] in (
                        "IsPreviousVersionOf", "IsVersionOf", "IsIdenticalTo"):
                    zeigt_auf[b["i"]] += 1
        if zeigt_auf:
            vertreter_id = zeigt_auf.most_common(1)[0][0]
            vertreter_grund = "quelle"
        else:
            vertreter_id = sorted(
                mitglieder, key=lambda m: (-(m["publikationsjahr"] or 0), m["id"]))[0]["id"]
            vertreter_grund = "juengster"
        vertreter = next(m for m in mitglieder if m["id"] == vertreter_id)

        # Widersprüche zwischen den Fassungen werden benannt, nicht geglättet: wenn
        # zwei Fassungen desselben Werks verschiedene Lizenzen tragen, ist das ein
        # Befund über die Quelle, kein Darstellungsproblem.
        abweichend = sorted({f for feld in ("lizenz_id", "herausgeber")
                             for f in [feld]
                             if len({(m[feld] or "") for m in mitglieder}) > 1})
        werke[werk_id] = {
            "t": vertreter["titel"],
            "h": vertreter["herausgeber"] or "",
            "v": vertreter_id,
            "vg": vertreter_grund,
            "n": len(mitglieder),
            "abw": abweichend,
            # Zugriffsweg und Quell-Id je Fassung wandern mit auf die Werk-Seite:
            # Sie standen bisher nur auf den Fassungsseiten, und die gibt es für
            # Mehrfassungs-Werke nicht mehr. Ohne sie verlöre die Umstellung genau
            # das, was das Register ausmacht — den wörtlichen Zugriffsweg je Eintrag.
            "f": sorted(({"i": m["id"], "t": m["titel"], "j": m["publikationsjahr"],
                          "l": m["lizenz_id"] or "", "q": m["quelle"],
                          "pv": m["zugang_geprueft"], "s": m["zugang_http_status"],
                          "u": m["zugang_url"] or "",
                          "p": (details.get(m["id"]) or {}).get("quell_id", "")}
                         for m in mitglieder),
                        key=lambda m: (-(m["j"] or 0), m["i"])),
        }

    # ---- Liste der Oberfläche: eine Zeile je INDEXIERBARER Seite ----
    # Nicht je Eintrag. Sonst stünden 24 Zeilen mit demselben Titel in der Liste, die
    # alle auf dieselbe Werk-Seite zeigen. Eine Zeile ist entweder ein Werk (mehrere
    # Fassungen) oder ein Eintrag ohne Geschwister. Angaben stammen vom Vertreter;
    # wo die Fassungen einander widersprechen, sagt `abw` das, statt einen Wert zu
    # wählen und die anderen zu verschweigen.
    zeilen_je_id = {z["i"]: z for z in zeilen}
    liste = []
    for werk_id, w in werke.items():
        vertreter = zeilen_je_id.get(w["v"]) or zeilen_je_id[w["f"][0]["i"]]
        liste.append({**vertreter, "i": werk_id, "w": 1, "n": w["n"],
                      "t": w["t"], "abw": w["abw"] or None})
    in_werk = {v["i"] for w in werke.values() for v in w["f"]}
    for z in zeilen:
        if z["i"] not in in_werk:
            liste.append({**z, "w": 0, "n": 1, "abw": None})
    liste.sort(key=lambda z: z["i"])

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

    # Werk-Ebene getrennt: die Site baut daraus /datasets/work/<werk_id>. Getrennt
    # von eintraege.json, weil die Suche im Browser sie nicht braucht.
    (ZIEL / "werke.json").write_text(json.dumps(werke, ensure_ascii=False,
                                                separators=(",", ":")))

    # liste.json ist das, was der BROWSER lädt (Suche, Filter, Ergebnisliste):
    # eine Zeile je indexierbarer Seite. eintraege.json bleibt vollständig, weil die
    # Fassungsseiten daraus gebaut werden — es erreicht den Browser aber nicht mehr.
    (ZIEL / "liste.json").write_text(json.dumps(liste, ensure_ascii=False,
                                                separators=(",", ":")))
    with gzip.open(ZIEL / "liste.json.gz", "wt", encoding="utf-8") as f:
        json.dump(liste, f, ensure_ascii=False, separators=(",", ":"))

    einzeln = sum(1 for m in werk_mitglieder.values() if len(m) == 1)
    print(f"{len(zeilen)} Kernbestand-Einträge von {meta.get('eintraege')} im Bestand "
          f"→ {ZIEL}")
    print(f"  Werk-Seiten: {len(werke)} (Werke mit mehreren Fassungen); "
          f"{einzeln} Werke mit einer Fassung behalten ihre Eintragsseite "
          f"→ {len(werke) + einzeln} indexierbare Seiten statt {len(zeilen)}")
    for name in ("eintraege.json", "eintraege.json.gz", "details.json"):
        print(f"  {name:<20} {(ZIEL / name).stat().st_size / 1e6:.2f} MB")
    mit_beschreibung = sum(1 for d in details.values() if d.get("beschreibung"))
    print(f"  details: {len(details)} Einträge, davon {mit_beschreibung} mit Beschreibung "
          f"(erreicht den Browser nicht)")


if __name__ == "__main__":
    main()
