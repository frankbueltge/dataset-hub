#!/usr/bin/env python3
"""Leitet `register/massenherausgeber.json` aus der Herausgeber-Messung ab.

Die Liste ist Teil der Aufnahmeschranke (Neufassung §4, Stufe 1). Sie wird NICHT
von Hand gepflegt und nicht zur Bauzeit gerechnet, sondern hier einmal aus einer
Messung abgeleitet und versioniert committet — damit steht in der Datei, worauf
sich jede Zeile stützt, und eine wachsende Ernte ändert den Bestand nicht still.

## Das Kriterium: Einträge je Titelmuster

Maßgeblich ist, **wie viele Einträge sich einen Titel teilen** — nicht die Größe des
Herausgebers und auch nicht die Wiederholungs-RATE. Die Rate (1 − Muster/n) war der
erste Versuch und ist verworfen: sie ist größenabhängig. DataverseNO kam auf 0,91,
obwohl es 12.119 verschiedene Titelmuster führt — ein vielfältiges Repositorium, dessen
Rate nur deshalb hoch ist, weil n groß ist. Gemessen (2026-07-27, ganzer Dump):

    je Muster    Einträge    Muster   Herausgeber
     196.234    1.177.402         6   Cambridge Crystallographic Data Centre
     110.383    3.201.093        29   UNITE Community
     108.144   29.198.792       270   National Institute for Fusion Science
      19.716      492.888        25   Environmental Molecular Sciences Laboratory
       3.050    4.007.397     1.314   GBIF („Occurrence Download")
         100       60.448       604   Institut français d'archéologie orientale
    ------------------------------------------------------------- Schwelle 100
          16,5  1.036.508    62.935   Zenodo
          15,6     58.687     3.753   UCLA Dataverse
          11,5    139.699    12.119   DataverseNO
           5,3     50.266     9.555   Kaggle

## Was das Kriterium NICHT kann

**Die Musterzählung ist bei 50.000 gekappt** (sonst müsste ein Herausgeber mit 30 Mio.
Einträgen 30 Mio. Titel im Arbeitsspeicher halten). Für gekappte Herausgeber ist die
gemeldete Musterzahl eine Untergrenze — das Verhältnis ist damit eine OBERGRENZE und
taugt nicht zur Aufnahme in die Liste. Sie werden als unentscheidbar berichtet.

**Kleine Serien fallen durch.** Ein Herausgeber mit 4.871 durchnummerierten Objekten
(Consiglio Nazionale delle Ricerche: „A 40-3", „Ja #", „CIH #") kommt auf 9,4 Einträge
je Muster und bleibt unter jeder sinnvollen Schwelle.

Beides wird nicht weggerechnet, sondern über `--urteile` entschieden: eine Datei mit
begründeten Einzelfällen, die in die Liste einfließen und dort ihre Herkunft behalten
(`herkunft: "urteil"` statt `"regel"`). Die Messung schlägt vor, die Liste entscheidet.
"""
import argparse
import json
import pathlib
import sys

from mess_lib import BASIS, ERGEBNISSE, heute, jetzt

REGISTER = BASIS.parent / "register"

# Ab so vielen Einträgen je Titelmuster gilt ein Herausgeber als Massenregistrant.
# Gemessen liegt die Lücke zwischen 16,5 (Zenodo) und 100 (IFAO); 100 liegt am oberen
# Rand dieser Lücke — bewusst vorsichtig, damit kein Repositorium hineinrutscht. Der
# Preis ist, dass kleinere Serien durchgehen; sie kosten Platz im Bestand, aber nicht
# die Oberfläche (dort entscheidet Stufe 2).
SCHWELLE_JE_MUSTER = 100

# Unterhalb dieser Zahl lohnt die Frage nicht: wenige Einträge mit ähnlichen Titeln
# sind eine kleine Serie, keine Massenregistrierung — und ihr Ausschluss brächte
# nichts, während ein Fehlgriff einen ganzen kleinen Herausgeber kostete.
SCHWELLE_ANZAHL = 200


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--messung", default=str(ERGEBNISSE / f"{heute()}-herausgeber-gesamt.json"),
                   help="Ergebnis-JSON von messe_herausgeber_gesamt.py")
    p.add_argument("--urteile", default=str(REGISTER / "massenherausgeber-urteile.json"),
                   help="begründete Einzelfälle, die das Maß nicht entscheiden kann")
    p.add_argument("--schreiben", action="store_true",
                   help="register/massenherausgeber.json tatsächlich schreiben")
    args = p.parse_args()

    pfad = pathlib.Path(args.messung)
    if not pfad.exists():
        sys.exit(f"Messung fehlt: {pfad} — erst messe_herausgeber_gesamt.py laufen lassen.")
    messung = json.loads(pfad.read_text(encoding="utf-8"))
    idx = {h["herausgeber"]: h for h in messung["herausgeber"]}

    treffer, unentscheidbar = [], []
    for h in messung["herausgeber"]:
        if not h["herausgeber"] or h["n"] < SCHWELLE_ANZAHL:
            continue
        muster = max(h["titel_muster_verschieden"], 1)
        je_muster = h["n"] / muster
        if h["titel_muster_gekappt"]:
            # Gekappt heißt: die gemeldete Musterzahl ist eine UNTERGRENZE, das
            # Verhältnis also eine OBERGRENZE. Eine Aufnahme lässt sich damit nie
            # begründen. Berichtet werden ALLE großen gekappten Herausgeber — auch
            # die unterhalb der Schwelle: dort ist die Obergrenze zwar erfüllt
            # ("liegt sicher darunter"), aber die Kappung ist genau der blinde Fleck
            # dieser Messung, und ein blinder Fleck, den niemand sieht, ist keiner.
            unentscheidbar.append({
                "herausgeber": h["herausgeber"], "n": h["n"],
                "titel_muster_mindestens": h["titel_muster_verschieden"],
                "je_muster_hoechstens": round(je_muster, 1),
                "ueber_schwelle_moeglich": je_muster >= SCHWELLE_JE_MUSTER,
                "grund": ("Musterzählung gekappt — Verhältnis ist nur eine Obergrenze; "
                          "mechanisch nicht als Massenherausgeber begründbar"),
                "titel_beispiele": h.get("titel_beispiele")})
            continue
        if je_muster >= SCHWELLE_JE_MUSTER:
            treffer.append({
                "name": h["herausgeber"],
                "herkunft": "regel",
                "n": h["n"],
                "titel_muster_verschieden": h["titel_muster_verschieden"],
                "eintraege_je_muster": round(je_muster, 1),
                "granularitaet": h.get("granularitaet"),
                "titel_beispiele": h.get("titel_beispiele"),
                "grund": (f"{h['n']:,} Einträge auf {h['titel_muster_verschieden']:,} "
                          f"Titelmuster ({je_muster:,.0f} je Muster) — "
                          f"Massenregistrierung einzelner Beobachtungen"),
            })

    # Begründete Einzelfälle: was das Maß nicht entscheiden kann, entscheidet ein
    # Urteil mit Beleg — nicht eine nachgebogene Schwelle.
    urteile_pfad = pathlib.Path(args.urteile)
    if urteile_pfad.exists():
        for u in json.loads(urteile_pfad.read_text(encoding="utf-8"))["herausgeber"]:
            gemessen = idx.get(u["name"], {})
            treffer.append({
                "name": u["name"],
                "herkunft": "urteil",
                "n": gemessen.get("n"),
                "titel_muster_verschieden": gemessen.get("titel_muster_verschieden"),
                "titel_muster_gekappt": gemessen.get("titel_muster_gekappt"),
                "titel_beispiele": gemessen.get("titel_beispiele"),
                "grund": u["beleg"],
            })
    else:
        print(f"HINWEIS: keine Urteilsdatei unter {urteile_pfad} — "
              f"nur maschinell entschiedene Herausgeber in der Liste.")

    treffer.sort(key=lambda t: -(t["n"] or 0))
    liste = {
        "fassung": 1,
        "datum": heute(),
        "erzeugt": jetzt(),
        "zweck": ("Aufnahmeschranke Stufe 1 der Neufassung des Registerzwecks "
                  "(frankbueltge.de → docs/design/2026-07-27-register-neufassung.md, §4). "
                  "Einträge dieser Herausgeber werden NICHT aufgenommen — es sei denn, "
                  "der Eintrag bezeichnet die Sammlung statt des Einzelstücks "
                  "(granularitaet 'collection' oder 'series')."),
        "grundlage": str(pfad.relative_to(BASIS.parent)),
        "kriterium": {"eintraege_je_titelmuster_mindestens": SCHWELLE_JE_MUSTER,
                      "eintraege_mindestens": SCHWELLE_ANZAHL,
                      "erlaeuterung": "Einträge geteilt durch verschiedene Titelmuster; "
                                      "Ziffernfolgen im Titel zu '#' normalisiert. "
                                      "Gekappte Zählungen entscheiden nicht mit."},
        "abgeleitet_von": "messungen/skripte/leite_massenherausgeber_ab.py",
        "herausgeber": treffer,
        "unentscheidbar": unentscheidbar,
    }

    per_regel = [t for t in treffer if t["herkunft"] == "regel"]
    per_urteil = [t for t in treffer if t["herkunft"] == "urteil"]
    print(f"{len(per_regel)} Massenherausgeber über der Schwelle "
          f"(≥ {SCHWELLE_JE_MUSTER} Einträge je Muster, n ≥ {SCHWELLE_ANZAHL}):")
    for t in per_regel[:15]:
        print(f"  {t['n']:>11,}  {t['eintraege_je_muster']:>9,.0f} je Muster  {t['name'][:52]}")
    if len(per_regel) > 15:
        print(f"  … und {len(per_regel) - 15} weitere")
    if per_urteil:
        print(f"\n{len(per_urteil)} per Urteil aufgenommen:")
        for t in per_urteil:
            print(f"  {(t['n'] or 0):>11,}  {t['name'][:52]}")
            print(f"               {t['grund'][:88]}")
    if unentscheidbar:
        print(f"\n{len(unentscheidbar)} unentscheidbar (Musterzählung gekappt) — "
              f"NICHT auf der Liste, brauchen ein Urteil:")
        for u in unentscheidbar:
            print(f"  {u['n']:>11,}  ≤{u['je_muster_hoechstens']:>8,.0f} je Muster  "
                  f"{u['herausgeber'][:48]}")
    betroffen = sum(t["n"] or 0 for t in treffer)
    gesamt = messung["zeilen_gesamt"]
    print(f"\nbetroffen: {betroffen:,} von {gesamt:,} Fundstellen "
          f"({betroffen / gesamt:.1%})")

    if args.schreiben:
        REGISTER.mkdir(exist_ok=True)
        ziel = REGISTER / "massenherausgeber.json"
        ziel.write_text(json.dumps(liste, indent=2, ensure_ascii=False) + "\n")
        print(f"\ngeschrieben: {ziel}")
    else:
        print("\n(Probelauf — mit --schreiben wird register/massenherausgeber.json erzeugt)")


if __name__ == "__main__":
    main()
