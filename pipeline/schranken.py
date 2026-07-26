"""Harte Schranken der Auto-Aufnahme (Design §3.4, Schema v0.1).

Rückgabe: None = aufgenommen (als 'ungeprueft'), sonst Grundcode für das
Ablehnungsregister. Die Schranken erfinden nichts und raten nichts — sie prüfen
nur, ob die Quelle das Minimum wörtlich mitliefert.
"""
AUSGESCHLOSSENE_STUFEN = {"purchase", "closed"}
# DataCite: nur "findable" ist öffentlich. HuggingFace: "disabled"/"private" sind
# quellenseitige Zustände mit derselben Bedeutung ("nicht öffentlich abrufbar"),
# wiederverwendet statt eines eigenen Vokabulars je Quelle.
ZURUECKGEZOGENE_STATI = {"registered", "draft", "disabled", "private"}


def pruefe(eintrag: dict):
    if not (eintrag.get("titel") or "").strip():
        return "kein-titel"
    zugang = eintrag.get("zugang") or {}
    if not (zugang.get("url") or "").strip():
        return "keine-zugangs-url"
    if not (eintrag.get("urheber") or (eintrag.get("herausgeber") or "").strip()):
        return "kein-urheber-oder-herausgeber"
    if not eintrag.get("identifikatoren"):
        return "keine-quell-pid"
    if (eintrag.get("quell_status") or "") in ZURUECKGEZOGENE_STATI:
        return "quellstatus-nicht-oeffentlich"
    if (zugang.get("stufe") or "") in AUSGESCHLOSSENE_STUFEN:
        return "zugangsstufe-ausgeschlossen"
    # Quellen-Ausnahme HuggingFace (schema/SCHEMA.md): eine aus dem API-Vertrag
    # KONSTRUIERTE Zugriffs-URL (kein wörtliches URL-Feld in der Quelle) darf nie
    # ohne bestätigte HTTP-Auflösung in den Bestand. Der Normalisierer markiert
    # solche Einträge mit zugang.url_konstruiert; baue_bestand.py heftet eine
    # vorliegende Auflösung aus pruefungen/aufloesungen.jsonl VOR diesem Aufruf an,
    # damit 'geprueft' hier bereits den tatsächlichen Stand zeigt.
    if zugang.get("url_konstruiert") and zugang.get("geprueft") not in ("landing", "download"):
        return "konstruierte-url-ungeprueft"
    return None
