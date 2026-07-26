"""Harte Schranken der Auto-Aufnahme (Design §3.4, Schema v0.1).

Rückgabe: None = aufgenommen (als 'ungeprueft'), sonst Grundcode für das
Ablehnungsregister. Die Schranken erfinden nichts und raten nichts — sie prüfen
nur, ob die Quelle das Minimum wörtlich mitliefert.
"""
AUSGESCHLOSSENE_STUFEN = {"purchase", "closed"}
ZURUECKGEZOGENE_STATI = {"registered", "draft"}  # DataCite: nur "findable" ist öffentlich


def pruefe(eintrag: dict):
    if not (eintrag.get("titel") or "").strip():
        return "kein-titel"
    if not ((eintrag.get("zugang") or {}).get("url") or "").strip():
        return "keine-zugangs-url"
    if not (eintrag.get("urheber") or (eintrag.get("herausgeber") or "").strip()):
        return "kein-urheber-oder-herausgeber"
    if not eintrag.get("identifikatoren"):
        return "keine-quell-pid"
    if (eintrag.get("quell_status") or "") in ZURUECKGEZOGENE_STATI:
        return "quellstatus-nicht-oeffentlich"
    if ((eintrag.get("zugang") or {}).get("stufe") or "") in AUSGESCHLOSSENE_STUFEN:
        return "zugangsstufe-ausgeschlossen"
    return None
