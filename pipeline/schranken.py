"""Harte Schranken der Auto-Aufnahme (Design §3.4, Schema v0.1).

Rückgabe: None = aufgenommen (als 'ungeprueft'), sonst Grundcode für das
Ablehnungsregister. Die Schranken erfinden nichts und raten nichts — sie prüfen
nur, ob die Quelle das Minimum wörtlich mitliefert.
"""
AUSGESCHLOSSENE_STUFEN = {"purchase", "closed"}

# Quellen, deren Nutzungsbedingungen der Aufnahme entgegenstehen oder ungeklärt sind.
# Die Rohernten bleiben im Archiv (nichts wird gelöscht), aber die Einträge erscheinen
# nicht im Bestand und damit nicht auf der Oberfläche. Rücknahme = Zeile entfernen.
# Belege je Quelle: messungen/register.md, Abschnitt „Rechtliche Grundlage je Quelle".
QUELLEN_ZURUECKGEHALTEN = {
    "kaggle": "quelle-rechtlich-ungeklaert",
}
# DataCite: nur "findable" ist öffentlich. HuggingFace: "disabled"/"private" sind
# quellenseitige Zustände mit derselben Bedeutung ("nicht öffentlich abrufbar"),
# wiederverwendet statt eines eigenen Vokabulars je Quelle.
ZURUECKGEZOGENE_STATI = {"registered", "draft", "disabled", "private"}


def pruefe(eintrag: dict):
    quelle = (eintrag.get("fundstellen") or [{}])[0].get("quelle") or ""
    if quelle in QUELLEN_ZURUECKGEHALTEN:
        return QUELLEN_ZURUECKGEHALTEN[quelle]
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
