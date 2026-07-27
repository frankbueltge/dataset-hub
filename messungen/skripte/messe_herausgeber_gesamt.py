#!/usr/bin/env python3
"""Herausgeber-Verteilung über ALLE lokalen Rohernten — exakt, nicht per Stichprobe.

Anlass: Die Neufassung des Registerzwecks (frankbueltge.de →
docs/design/2026-07-27-register-neufassung.md) macht ein Relevanzkriterium nötig.
Dessen erste Stufe schließt Massenregistrierungen einzelner Beobachtungen aus. Welche
Herausgeber das sind, stand bisher nur aus einer 400.000er-Stichprobe fest
(2026-07-27-dump-zusammensetzung.md). Für eine Schranke, die dauerhaft im Bau steht,
ist eine Stichprobe zu wenig: sie entscheidet über Aufnahme und Ablehnung.

Liest jede Fundstellen-Datei einmal im Strom (nichts wird im Ganzen geladen) und zählt
je (Quelle, Herausgeber): Anzahl, Granularitäten, Lizenzen, Jahre, Titel-Beispiele und
die Titel-Wiederholungsrate. Letztere ist der eigentliche Serien-Indikator: eine
Massenregistrierung vergibt tausendfach denselben oder einen nur durchnummerierten
Titel, eine kuratierte Sammlung nicht.

Nur Standardbibliothek (Bauregel). Kein Netzzugriff — die Rohernten liegen lokal.
"""
import collections
import gzip
import hashlib
import json
import multiprocessing
import pathlib
import sys

from mess_lib import BASIS, ERGEBNISSE, ROHDATEN, heute, jetzt

FUNDSTELLEN = BASIS.parent / "fundstellen"

# Unterhalb dieser Einträgezahl wird ein Herausgeber im committeten Ergebnis nicht
# einzeln geführt (die volle Zählung liegt gezippt bei den Rohdaten). Der Wert ist
# dieselbe Schwelle, ab der leite_massenherausgeber_ab.py überhaupt hinsieht — was
# darunter liegt, kann das Kriterium ohnehin nicht erreichen.
BERICHTSSCHWELLE = 200

# Titel-Wiederholungsrate: je Herausgeber werden höchstens so viele verschiedene
# Titel gemerkt. Danach zählt das Skript nur weiter, ohne die Menge wachsen zu lassen.
# Ohne diese Kappung müsste ein Herausgeber mit 30 Mio. Einträgen 30 Mio. Titel im
# Arbeitsspeicher halten. Die Rate ist dadurch eine untere Schranke der Wiederholung
# — sie kann Serien unterschätzen, nie übertreiben.
TITEL_KAPPUNG = 50_000


def _feld(roh: dict, quelle: str):
    """Herausgeber, Granularität, Lizenz, Jahr, Titel — wörtlich, je Quellenschema.

    Bewusst eine eigene, schlanke Extraktion statt pipeline/normalisiere.py: die
    Messung soll den ROHSTAND zeigen, nicht den bereits normalisierten. Weicht die
    Normalisierung später ab, ist das ein Befund und kein stiller Gleichlauf.
    """
    if quelle == "datacite":
        p = roh.get("publisher")
        herausgeber = (p.get("name") if isinstance(p, dict) else p) or ""
        granularitaet = ((roh.get("types") or {}).get("resourceTypeGeneral") or "")
        lizenz = ""
        for r in roh.get("rightsList") or []:
            lizenz = (r.get("rightsIdentifier") or "") or lizenz
            if lizenz:
                break
        jahr = roh.get("publicationYear")
        titel = ""
        for t in roh.get("titles") or []:
            titel = (t.get("title") or "").strip()
            if titel:
                break
        return herausgeber, granularitaet, lizenz, jahr, titel
    if quelle == "arcgis":
        attr = roh.get("attributes") or {}
        struk = attr.get("structuredLicense")
        lizenz = (struk.get("type") or struk.get("abbr") or "") if isinstance(struk, dict) else ""
        return ((attr.get("orgName") or attr.get("organization") or attr.get("source") or ""),
                (attr.get("type") or ""), lizenz, None, (attr.get("name") or "").strip())
    if quelle == "huggingface":
        card = roh.get("cardData") or {}
        lizenz = card.get("license")
        if isinstance(lizenz, list):
            lizenz = lizenz[0] if lizenz else ""
        hf_id = (roh.get("id") or "")
        # HuggingFace führt kein Herausgeberfeld; der Namensraum vor "/" ist das
        # nächstliegende wörtliche Äquivalent (so zeigt die Quelle es selbst an).
        return (hf_id.split("/", 1)[0] if "/" in hf_id else ""), "dataset", (lizenz or ""), None, \
            (card.get("pretty_name") or hf_id)
    return "", "", "", None, ""


def _titel_muster(titel: str) -> str:
    """Titel auf sein Muster reduzieren: alle Ziffernfolgen werden zu '#'.

    'Shot 123456' und 'Shot 123457' fallen damit auf dasselbe Muster zusammen. Genau
    das unterscheidet eine durchnummerierte Serie von einer Sammlung eigenständiger
    Titel — ohne Ziffernnormalisierung wäre jeder Messschuss ein 'eigener' Titel.
    """
    aus, in_zahl = [], False
    for z in titel:
        if z.isdigit():
            if not in_zahl:
                aus.append("#")
                in_zahl = True
        else:
            aus.append(z)
            in_zahl = False
    return "".join(aus)[:120]


def _quelle_aus_name(pfad: pathlib.Path) -> str:
    return pfad.name.split("-", 1)[0]


def zaehle_datei(pfad_str: str) -> dict:
    """Ein Teil, ein Durchlauf. Rückgabe ist serialisierbar (Prozessgrenze)."""
    pfad = pathlib.Path(pfad_str)
    quelle = _quelle_aus_name(pfad)
    je_herausgeber = collections.defaultdict(
        lambda: {"n": 0, "granularitaet": collections.Counter(), "lizenz": collections.Counter(),
                 "jahr": collections.Counter(), "titel_muster": set(), "titel_beispiele": [],
                 "titel_gezaehlt": 0, "muster_gekappt": False})
    zeilen, kaputt = 0, 0
    with gzip.open(pfad, "rt", encoding="utf-8") as f:
        for zeile in f:
            zeilen += 1
            try:
                fund = json.loads(zeile)
            except Exception:
                kaputt += 1          # nie überbrücken: defekte Zeilen werden berichtet
                continue
            roh = fund.get("roh") or {}
            herausgeber, gran, lizenz, jahr, titel = _feld(roh, fund.get("quelle") or quelle)
            e = je_herausgeber[herausgeber]
            e["n"] += 1
            e["granularitaet"][gran] += 1
            e["lizenz"][lizenz] += 1
            e["jahr"][str(jahr) if jahr else ""] += 1
            if titel:
                e["titel_gezaehlt"] += 1
                if len(e["titel_muster"]) < TITEL_KAPPUNG:
                    e["titel_muster"].add(_titel_muster(titel))
                else:
                    e["muster_gekappt"] = True
                if len(e["titel_beispiele"]) < 3:
                    e["titel_beispiele"].append(titel[:160])
    return {"datei": pfad.name, "quelle": quelle, "zeilen": zeilen, "kaputte_zeilen": kaputt,
            "je_herausgeber": {h: {"n": e["n"], "granularitaet": dict(e["granularitaet"]),
                                   "lizenz": dict(e["lizenz"]), "jahr": dict(e["jahr"]),
                                   "titel_muster": list(e["titel_muster"]),
                                   "titel_beispiele": e["titel_beispiele"],
                                   "titel_gezaehlt": e["titel_gezaehlt"],
                                   "muster_gekappt": e["muster_gekappt"]}
                               for h, e in je_herausgeber.items()}}


def main():
    dateien = sorted(FUNDSTELLEN.glob("*.jsonl.gz"))
    if not dateien:
        sys.exit("keine Fundstellen gefunden — nichts zu messen")
    print(f"{len(dateien)} Dateien, "
          f"{sum(p.stat().st_size for p in dateien) / 1e9:.1f} GB gz")

    # Sofort zusammenführen statt alle Teilergebnisse zu sammeln: ein Teilergebnis
    # kann je Herausgeber bis zu TITEL_KAPPUNG Muster enthalten — über 114 Teile
    # gehalten wären das mehrere hundert MB, die niemand braucht.
    gesamt = collections.defaultdict(
        lambda: {"n": 0, "granularitaet": collections.Counter(), "lizenz": collections.Counter(),
                 "jahr": collections.Counter(), "titel_muster": set(), "titel_beispiele": [],
                 "titel_gezaehlt": 0, "muster_gekappt": False, "quellen": collections.Counter()})
    zeilen_gesamt = kaputt_gesamt = 0
    je_quelle = collections.Counter()

    prozesse = max(1, (multiprocessing.cpu_count() or 2) - 2)
    with multiprocessing.Pool(prozesse) as pool:
        for i, teil in enumerate(pool.imap_unordered(
                zaehle_datei, [str(p) for p in dateien]), 1):
            zeilen_gesamt += teil["zeilen"]
            kaputt_gesamt += teil["kaputte_zeilen"]
            je_quelle[teil["quelle"]] += teil["zeilen"]
            for h, e in teil["je_herausgeber"].items():
                g = gesamt[h]
                g["n"] += e["n"]
                g["quellen"][teil["quelle"]] += e["n"]
                g["granularitaet"].update(e["granularitaet"])
                g["lizenz"].update(e["lizenz"])
                g["jahr"].update(e["jahr"])
                g["titel_gezaehlt"] += e["titel_gezaehlt"]
                # Kappung eines Teils ist auch eine Kappung des Ganzen: die
                # Wiederholungsrate wäre sonst aus unvollständigen Mustern gerechnet.
                g["muster_gekappt"] = g["muster_gekappt"] or e["muster_gekappt"]
                if len(g["titel_muster"]) < TITEL_KAPPUNG:
                    g["titel_muster"].update(e["titel_muster"])
                else:
                    g["muster_gekappt"] = True
                for t in e["titel_beispiele"]:
                    if len(g["titel_beispiele"]) < 3:
                        g["titel_beispiele"].append(t)
            print(f"  [{i}/{len(dateien)}] {teil['datei']}: {teil['zeilen']} Zeilen", flush=True)

    herausgeber = []
    for h, g in sorted(gesamt.items(), key=lambda kv: -kv[1]["n"]):
        muster = len(g["titel_muster"])
        # Wiederholungsrate: 1 - (verschiedene Titelmuster / gezählte Titel).
        # 0,999 heißt: auf 1000 Einträge kommt ein eigenständiger Titel.
        rate = (round(1 - muster / g["titel_gezaehlt"], 4)
                if g["titel_gezaehlt"] and not g["muster_gekappt"] else None)
        herausgeber.append({
            "herausgeber": h,
            "n": g["n"],
            "anteil": round(g["n"] / zeilen_gesamt, 6) if zeilen_gesamt else None,
            "quellen": dict(g["quellen"]),
            "granularitaet": dict(g["granularitaet"].most_common(6)),
            "lizenz_top": dict(g["lizenz"].most_common(6)),
            "jahr_top": dict(g["jahr"].most_common(6)),
            "titel_muster_verschieden": muster,
            "titel_gezaehlt": g["titel_gezaehlt"],
            "titel_muster_gekappt": g["muster_gekappt"],
            "titel_wiederholungsrate": rate,
            "titel_beispiele": g["titel_beispiele"],
        })

    # Rohdaten-Deckung: die Fundstellen-Dateien selbst sind die Rohdaten dieser
    # Messung (sie liegen wegen ihrer Größe außerhalb von git). Statt sie zu kopieren,
    # wird ihre Identität festgehalten — Größe und SHA-256 der ersten 1 MiB je Datei,
    # damit nachprüfbar bleibt, WORAUF gemessen wurde.
    deckung = []
    for p in dateien:
        with open(p, "rb") as f:
            kopf = hashlib.sha256(f.read(1024 * 1024)).hexdigest()
        deckung.append({"datei": p.name, "bytes": p.stat().st_size, "sha256_erste_mib": kopf})

    ERGEBNISSE.mkdir(exist_ok=True)
    ROHDATEN.mkdir(exist_ok=True)
    ergebnis = {
        "quelle": "herausgeber-gesamt",
        "erzeugt": jetzt(),
        "verfahren": "vollstaendiger Durchlauf aller lokalen Rohernten, keine Stichprobe",
        "zeilen_gesamt": zeilen_gesamt,
        "kaputte_zeilen": kaputt_gesamt,
        "zeilen_je_quelle": dict(je_quelle),
        "herausgeber_verschieden": len(herausgeber),
        "titel_kappung": TITEL_KAPPUNG,
        "dateien": deckung,
        "herausgeber": herausgeber,
    }

    # Die volle Zählung über 18.350 Herausgeber ist 14 MB groß — das 800-fache jeder
    # anderen Messung dieses Repos und nichts, was in die Git-Historie gehört. Sie
    # wandert gezippt zu den Rohdaten; committet wird ein Ergebnis, das nur die
    # Herausgeber führt, die für das Kriterium überhaupt in Frage kommen. Die Deckung
    # bleibt damit gewahrt: jede berichtete Zahl steht in den Rohdaten.
    roh_pfad = ROHDATEN / f"{heute()}-herausgeber-gesamt-vollstaendig.json.gz"
    with gzip.open(roh_pfad, "wt", encoding="utf-8") as f:
        json.dump(ergebnis, f, ensure_ascii=False)

    gekuerzt = dict(ergebnis)
    gekuerzt["herausgeber"] = [h for h in herausgeber if h["n"] >= BERICHTSSCHWELLE]
    gekuerzt["berichtsschwelle"] = BERICHTSSCHWELLE
    gekuerzt["herausgeber_unter_schwelle"] = len(herausgeber) - len(gekuerzt["herausgeber"])
    gekuerzt["vollstaendige_zaehlung"] = str(roh_pfad.relative_to(BASIS))

    pfad = ERGEBNISSE / f"{heute()}-herausgeber-gesamt.json"
    pfad.write_text(json.dumps(gekuerzt, indent=2, ensure_ascii=False) + "\n")
    print(f"\ngeschrieben: {pfad} ({len(gekuerzt['herausgeber'])} Herausgeber "
          f"ab {BERICHTSSCHWELLE} Einträgen)")
    print(f"vollstaendige Zaehlung: {roh_pfad}")
    print(f"{zeilen_gesamt} Zeilen, {len(herausgeber)} Herausgeber, "
          f"{kaputt_gesamt} kaputte Zeilen")


if __name__ == "__main__":
    main()
