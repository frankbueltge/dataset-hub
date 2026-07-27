"""Relevanzkriterium der Neufassung (frankbueltge.de →
docs/design/2026-07-27-register-neufassung.md, §4). Zwei Stufen:

    Stufe 1 — Materialgüte: entscheidet über die AUFNAHME in den Bestand.
              Deterministisch, thematisch offen. Ergebnis ist der Snapshot,
              den die Praxen abfragen.
    Stufe 2 — Kernbestand: ein MERKMAL am aufgenommenen Eintrag. Nur der
              Kernbestand bekommt Unterseiten und Sichtbarkeit auf der Website.

Beide Stufen erfinden nichts. Sie lesen nur, was die Quelle wörtlich mitliefert,
und begründen jede Ablehnung mit einem Grundcode fürs Register.
"""
import json
import pathlib
import re

WURZEL = pathlib.Path(__file__).resolve().parent.parent
MASSENHERAUSGEBER_DATEI = WURZEL / "register" / "massenherausgeber.json"

# Granularitäten, die eine SAMMLUNG bezeichnen statt eines Einzelstücks. Ein Eintrag
# eines Massenherausgebers auf dieser Ebene ist genau das, was das Register will —
# „es sei denn, ein Eintrag bezeichnet die Sammlung statt des Einzelstücks" (§4).
SAMMLUNGS_GRANULARITAETEN = {"collection", "series"}

# Platzhalter, die zwar in einem Lizenzfeld stehen, aber keine Lizenz BENENNEN.
# „custom" ist der häufigste: die Quelle sagt damit ausdrücklich, dass sie den
# Rechtsstand nicht in einem bekannten Bezeichner ausdrücken kann.
LIZENZ_PLATZHALTER = {"", "custom", "none", "other", "unknown", "unlicensed",
                      "proprietary", "all-rights-reserved"}

# Offene Lizenzen nach der Open Definition: Weiterverwendung und Weitergabe erlaubt,
# Namensnennung und Share-alike zulässig. NC und ND sind bewusst NICHT dabei — sie
# schließen genau die Nutzung aus, für die das Register das Material nachweist.
# Die Prüfung läuft über normalisierte Präfixe, weil dieselbe Lizenz je Quelle als
# "cc-by-4.0", "CC-BY-4.0" oder "CC_BY_4_0" auftritt.
OFFENE_LIZENZ_PRAEFIXE = (
    "cc0", "cc-zero", "publicdomain", "pddl", "odc-pddl",
    "cc-by-1.0", "cc-by-2.0", "cc-by-2.5", "cc-by-3.0", "cc-by-4.0",
    "cc-by-sa-1.0", "cc-by-sa-2.0", "cc-by-sa-2.5", "cc-by-sa-3.0", "cc-by-sa-4.0",
    "odbl", "odc-by", "odc-odbl", "ogl", "dl-de-by", "etalab",
    "mit", "apache-2.0", "bsd-2-clause", "bsd-3-clause", "gpl-3.0", "lgpl-3.0",
)


def _normalisiere_lizenz(lizenz_id: str) -> str:
    """Bezeichner vergleichbar machen: Kleinschreibung, Trennzeichen vereinheitlicht.

    'CC_BY_4_0', 'CC BY 4.0' und 'cc-by-4.0' sind derselbe Rechtsstand; nur die
    Schreibweise unterscheidet die Quellen. Ein Trennzeichen ZWISCHEN ZIFFERN ist
    dabei immer ein Versionspunkt ('4-0' → '4.0'); die Ziffern verschmelzen aber
    nie, damit der Tippfehler 'cc-by-40' nicht als 'cc-by-4.0' durchgeht.
    """
    s = (lizenz_id or "").strip().lower().replace("_", "-").replace(" ", "-")
    s = re.sub(r"-+", "-", s).strip("-")
    return re.sub(r"(\d)-(\d)", r"\1.\2", s)


def lizenz_benannt(eintrag: dict) -> bool:
    """Stufe 1: Es steht ein Bezeichner da, der überhaupt etwas aussagt."""
    return _normalisiere_lizenz((eintrag.get("lizenz") or {}).get("id")) \
        not in LIZENZ_PLATZHALTER


def lizenz_offen(eintrag: dict) -> bool:
    """Stufe 2: Der Bezeichner ist eine offene Lizenz nach der Open Definition."""
    s = _normalisiere_lizenz((eintrag.get("lizenz") or {}).get("id"))
    if not s or s in LIZENZ_PLATZHALTER:
        return False
    # 'cc-by-nc-4.0' beginnt mit 'cc-by-' — der NC/ND-Ausschluss muss deshalb VOR
    # dem Präfixvergleich stehen, sonst rutschten die eingeschränkten Lizenzen durch.
    if re.search(r"(^|-)(nc|nd)(-|$)", s):
        return False
    return any(s.startswith(p) for p in OFFENE_LIZENZ_PRAEFIXE)


class Massenherausgeber:
    """Versionierte Liste der Herausgeber, die einzelne Beobachtungen massenhaft
    registrieren (ein DOI je Experimentschuss, je Sammlungsbeleg, je Fundmeldung).

    Bewusst eine gepflegte Liste mit Beleg und Begründung je Eintrag, nicht eine
    Schwelle, die zur Bauzeit gerechnet wird: eine gerechnete Schwelle änderte den
    Bestand still, sobald eine Ernte wächst. Die Liste ändert ihn nur, wenn jemand
    sie ändert — und dann steht der Grund daneben.
    """

    def __init__(self, namen: dict):
        self.namen = namen

    @classmethod
    def lade(cls, pfad: pathlib.Path = MASSENHERAUSGEBER_DATEI) -> "Massenherausgeber":
        if not pfad.exists():
            # Kein stiller Rückfall auf „leere Liste": ohne Liste greift die Schranke
            # nicht, und der Bestand füllte sich unbemerkt wieder mit Serien.
            raise FileNotFoundError(
                f"Massenherausgeber-Liste fehlt: {pfad}. Sie ist Teil der Aufnahme-"
                f"schranke (Neufassung §4, Stufe 1) — ohne sie darf kein Bestand bauen.")
        daten = json.loads(pfad.read_text(encoding="utf-8"))
        return cls({h["name"]: h for h in daten.get("herausgeber", [])})

    def trifft(self, eintrag: dict) -> bool:
        herausgeber = (eintrag.get("herausgeber") or "").strip()
        if herausgeber not in self.namen:
            return False
        # Die Ausnahme aus §4: bezeichnet der Eintrag die Sammlung selbst, bleibt er.
        return (eintrag.get("granularitaet") or "") not in SAMMLUNGS_GRANULARITAETEN


def pruefe_materialguete(eintrag: dict, massenherausgeber: Massenherausgeber):
    """Stufe 1. Rückgabe: None = aufnehmen, sonst Grundcode fürs Ablehnungsregister.

    Läuft NACH schranken.pruefe() — die harten Schranken prüfen, ob die Quelle das
    Minimum mitliefert; diese Stufe prüft, ob das Gelieferte als Material taugt.
    """
    if massenherausgeber.trifft(eintrag):
        return "massenregistrierung"
    if not lizenz_benannt(eintrag):
        return "lizenz-nicht-benannt"
    return None
