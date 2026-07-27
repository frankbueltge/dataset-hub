"""Normalisierung: Fundstelle → Eintrag (Schema v0.1). Fehlende Angaben bleiben leer."""
from hub_lib import hub_id, normalisiere_doi

GRANULARITAET = {"Dataset": "dataset", "Collection": "collection", "Service": "service"}


def _text(x) -> str:
    return x.strip() if isinstance(x, str) else ""


def _objekte(xs):
    """Nur die Objekte einer Quellenliste — alles andere überspringen.

    DataCite-Listen wie `nameIdentifiers`, `rightsList` oder `dates` sind laut Schema
    Listen von Objekten, enthalten im Public Data File aber vereinzelt blanke
    Zeichenketten. Gemessen am 27.07.: der Bulk-Abbau stürzte auf Teil 33 ab, weil ein
    `nameIdentifiers`-Eintrag ein String war. Solche Werte werden übersprungen, nicht
    gedeutet — aus 'ORCID-irgendwas' einen Identifikator zu raten hieße erfinden.
    """
    return [x for x in (xs or []) if isinstance(x, dict)]


def normalisiere_datacite(fund: dict) -> dict:
    roh = fund.get("roh") or {}
    doi = normalisiere_doi(roh.get("doi") or fund.get("quell_id"))

    titel = ""
    for t in _objekte(roh.get("titles")):
        titel = _text(t.get("title"))
        if titel:
            break

    beschreibung = ""
    for b in _objekte(roh.get("descriptions")):
        beschreibung = _text(b.get("description"))
        if beschreibung:
            break

    urheber = []
    for c in _objekte(roh.get("creators")):
        name = _text(c.get("name")) or " ".join(
            x for x in (_text(c.get("givenName")), _text(c.get("familyName"))) if x)
        if not name:
            continue
        orcid = ""
        for ni in _objekte(c.get("nameIdentifiers")):
            if (ni.get("nameIdentifierScheme") or "").lower() == "orcid":
                orcid = _text(ni.get("nameIdentifier"))
        eintrag = {"name": name}
        if orcid:
            eintrag["orcid"] = orcid
        urheber.append(eintrag)

    pub = roh.get("publisher")
    herausgeber = _text(pub.get("name")) if isinstance(pub, dict) else _text(pub)

    lizenz_id, lizenz_roh = "", []
    for r in _objekte(roh.get("rightsList")):
        lizenz_roh.append({k: v for k, v in r.items() if v})
        if not lizenz_id:
            lizenz_id = _text(r.get("rightsIdentifier"))

    daten = [{"datum": _text(d.get("date")), "typ": _text(d.get("dateType"))}
             for d in _objekte(roh.get("dates")) if _text(d.get("date"))]

    identifikatoren = [{"schema": "doi", "wert": doi}] if doi else []
    for a in _objekte(roh.get("alternateIdentifiers")):
        wert = _text(a.get("alternateIdentifier"))
        if wert:
            identifikatoren.append(
                {"schema": _text(a.get("alternateIdentifierType")).lower() or "unbekannt",
                 "wert": wert})

    relationen = []
    for rel in _objekte(roh.get("relatedIdentifiers")):
        ziel = _text(rel.get("relatedIdentifier"))
        if ziel:
            relationen.append({"typ": _text(rel.get("relationType")),
                               "ziel_schema": _text(rel.get("relatedIdentifierType")),
                               "ziel": ziel})

    typ_roh = ((roh.get("types") or {}).get("resourceTypeGeneral") or "")

    return {
        "id": hub_id("doi", doi) if doi else hub_id(fund.get("quelle", ""), fund.get("quell_id", "")),
        "granularitaet": GRANULARITAET.get(typ_roh, "dataset" if typ_roh else ""),
        "titel": titel,
        "beschreibung": beschreibung,
        "urheber": urheber,
        "herausgeber": herausgeber,
        "publikationsjahr": roh.get("publicationYear") or None,
        "daten": daten,
        "raeumlichkeit": roh.get("geoLocations") or [],
        "lizenz": {"id": lizenz_id, "roh": lizenz_roh},
        "zugang": {"stufe": "", "url": _text(roh.get("url")), "geprueft": "none",
                   "geprueft_am": "", "http_status": None, "finale_url": ""},
        "identifikatoren": identifikatoren,
        "relationen": relationen,
        "quell_status": _text(roh.get("state")),
        "status": "ungeprueft",
        "fundstellen": [{"quelle": fund.get("quelle"), "quell_id": fund.get("quell_id"),
                         "geerntet": fund.get("geerntet"),
                         "adapter_version": fund.get("adapter_version")}],
    }


def normalisiere_kaggle(fund: dict) -> dict:
    """Kaggle liefert eine wörtliche Zugriffs-URL (`url`) — anders als HuggingFace
    keine Quellen-Ausnahme nötig (Messung 2026-07-26-kaggle.md, Abschnitt 3).
    Quell-PID ist `ref` (z. B. "owner/dataset-slug")."""
    roh = fund.get("roh") or {}
    ref = _text(roh.get("ref") or fund.get("quell_id"))

    titel = _text(roh.get("title"))
    beschreibung = _text(roh.get("subtitle")) or _text(roh.get("description"))

    # Kaggle trägt Urheberschaft persönlich/account-bezogen (creatorName/ownerName),
    # kein separates Herausgeber-/Institutionsfeld beobachtet.
    autor = _text(roh.get("creatorName")) or _text(roh.get("ownerName"))
    urheber = [{"name": autor}] if autor else []

    # licenseName ist ein freies Textlabel (z. B. "CC0: Public Domain"), kein
    # formaler Identifier wie DataCites rightsIdentifier — deshalb lizenz.id leer
    # lassen und den Wortlaut nur in lizenz.roh bewahren (nichts erfinden).
    lizenz_name = _text(roh.get("licenseName"))
    lizenz_roh = [{"licenseName": lizenz_name}] if lizenz_name else []

    aktualisiert = _text(roh.get("lastUpdated"))
    daten = [{"datum": aktualisiert, "typ": "lastUpdated"}] if aktualisiert else []

    identifikatoren = [{"schema": "kaggle-ref", "wert": ref}] if ref else []

    return {
        "id": hub_id("kaggle-ref", ref) if ref
              else hub_id(fund.get("quelle", ""), fund.get("quell_id", "")),
        # API-Vertrag ist "Kaggle Datasets" — analog zur DataCite-Ressourcenart-
        # Filterung gilt jeder Treffer als "dataset", solange eine ref vorliegt.
        "granularitaet": "dataset" if ref else "",
        "titel": titel,
        "beschreibung": beschreibung,
        "urheber": urheber,
        "herausgeber": "",
        "publikationsjahr": None,
        "daten": daten,
        "raeumlichkeit": [],
        "lizenz": {"id": "", "roh": lizenz_roh},
        "zugang": {"stufe": "", "url": _text(roh.get("url")), "geprueft": "none",
                   "geprueft_am": "", "http_status": None, "finale_url": ""},
        "identifikatoren": identifikatoren,
        "relationen": [],
        "quell_status": "",
        "status": "ungeprueft",
        "fundstellen": [{"quelle": fund.get("quelle"), "quell_id": fund.get("quell_id"),
                         "geerntet": fund.get("geerntet"),
                         "adapter_version": fund.get("adapter_version")}],
    }


def normalisiere_arcgis(fund: dict) -> dict:
    """ArcGIS Hub zählt (Item × Layer)-Kombinationen, nicht Ressourcen (Messung
    2026-07-26-arcgis.md, Abschnitt 0: nur 51,5 % eindeutige itemId in der
    Stichprobe). quell_id ist deshalb bewusst `itemId`, NICHT der Layer-spezifische
    `id` — die generische "jüngste Fundstelle je (quelle, quell_id)"-Zusammenführung
    in baue_bestand.py reduziert Multi-Layer-Services dadurch bereits vor der
    Normalisierung auf einen Eintrag im Hub. Der Layer-spezifische `id` geht dabei
    nicht verloren, sondern wird als zusätzlicher Identifikator mitgeführt, damit
    die Mehrfachzählung nachvollziehbar bleibt statt still zu verschwinden.

    `roh` ist hier — anders als bei DataCite — das VOLLE JSON:API-Resource-Objekt
    (type/id/attributes/links), nicht nur `attributes`: `links.itemPage` (die
    Landingpage) liegt außerhalb von `attributes` und muss wörtlich erhalten
    bleiben (Auflage: Landingpage-Feld laut Messung 100 % belegt)."""
    roh = fund.get("roh") or {}
    attr = roh.get("attributes") or {}
    layer_id = _text(roh.get("id"))
    item_id = _text(attr.get("itemId")) or _text(fund.get("quell_id"))

    titel = _text(attr.get("name"))

    urheber = []
    besitzer = _text(attr.get("owner"))
    if besitzer:
        urheber.append({"name": besitzer})
    herausgeber = (_text(attr.get("orgName")) or _text(attr.get("organization"))
                   or _text(attr.get("source")))

    lizenz_roh, lizenz_id = [], ""
    lizenz_frei = attr.get("license")
    struk = attr.get("structuredLicense")
    if lizenz_frei:
        lizenz_roh.append({"license": lizenz_frei})
    if struk:
        lizenz_roh.append({"structuredLicense": struk})
        if isinstance(struk, dict):
            lizenz_id = _text(struk.get("type")) or _text(struk.get("abbr"))

    identifikatoren = [{"schema": "arcgis-item", "wert": item_id}] if item_id else []
    if layer_id and layer_id != item_id:
        identifikatoren.append({"schema": "arcgis-layer-id", "wert": layer_id})

    modified = attr.get("modified")
    daten = [{"datum": str(modified), "typ": "modified"}] if modified is not None else []

    landingpage = _text((roh.get("links") or {}).get("itemPage"))

    # Nur die in der Stichprobe beobachteten Typen abbilden (Feature/Raster/Mosaic
    # Layer, Table sind allesamt GIS-Dienst-Layer, kein flaches Datei-Dataset) —
    # unbekannte künftige `type`-Werte werden NICHT geraten, sondern bleiben leer.
    typ_roh = _text(attr.get("type"))
    ARCGIS_GRANULARITAET = {"Feature Layer": "service", "Raster Layer": "service",
                            "Mosaic Layer": "service", "Table": "file"}
    granularitaet = ARCGIS_GRANULARITAET.get(typ_roh, "")

    return {
        "id": hub_id("arcgis-item", item_id) if item_id
              else hub_id(fund.get("quelle", ""), fund.get("quell_id", "")),
        "granularitaet": granularitaet,
        "titel": titel,
        "beschreibung": "",
        "urheber": urheber,
        "herausgeber": herausgeber,
        "publikationsjahr": None,
        "daten": daten,
        "raeumlichkeit": [attr.get("extent")] if attr.get("extent") else [],
        "lizenz": {"id": lizenz_id, "roh": lizenz_roh},
        "zugang": {"stufe": "", "url": _text(attr.get("url")), "geprueft": "none",
                   "geprueft_am": "", "http_status": None, "finale_url": "",
                   "landingpage": landingpage},
        "identifikatoren": identifikatoren,
        "relationen": [],
        "quell_status": "",
        "status": "ungeprueft",
        "fundstellen": [{"quelle": fund.get("quelle"), "quell_id": fund.get("quell_id"),
                         "geerntet": fund.get("geerntet"),
                         "adapter_version": fund.get("adapter_version")}],
    }


def normalisiere_huggingface(fund: dict) -> dict:
    """HuggingFace führt kein URL-Feld (Messung 2026-07-26-huggingface.md,
    Abschnitt 3+6). Genehmigte Quellen-Ausnahme (schema/SCHEMA.md, Abschnitt
    "Quellen-Ausnahme", Frank 2026-07-26): der Zugriffsweg wird hier aus dem
    dokumentierten API-Vertrag der Quelle GEBILDET (huggingface.co/datasets/<id>)
    — aber ein solcher Eintrag darf NIE ohne bestätigte HTTP-Auflösung in den
    Bestand. Das Merkmal `zugang.url_konstruiert` markiert genau das für
    schranken.py (Grundcode 'konstruierte-url-ungeprueft'); baue_bestand.py heftet
    eine vorliegende Auflösung aus pruefungen/aufloesungen.jsonl VOR der
    Schranken-Prüfung an, damit `geprueft` dort bereits den tatsächlichen Stand
    zeigt statt immer nur den Anfangswert 'none'."""
    roh = fund.get("roh") or {}
    hf_id = _text(roh.get("id") or fund.get("quell_id"))

    titel = _text((roh.get("cardData") or {}).get("pretty_name"))
    if not titel:
        # id ("org/name") ist ein wörtliches Quellfeld, kein erfundener Titel —
        # HuggingFace selbst zeigt id als Überschrift, wenn pretty_name fehlt
        # (62,5 % Abdeckung laut Messung; id ist dagegen zu 100 % belegt).
        titel = hf_id

    beschreibung = _text(roh.get("description"))

    # `author` ist ein eigenes, wörtliches Feld im Detail-Datensatz; Rückfallebene
    # ist der Namensraum-Teil der id (vor dem ersten "/"), ebenfalls wörtlich.
    autor = _text(roh.get("author"))
    if not autor and "/" in hf_id:
        autor = hf_id.split("/", 1)[0]
    urheber = [{"name": autor}] if autor else []

    # Lizenz aus Tag "license:*" (tags-Liste) oder cardData.license (String ODER
    # Liste — beide Formen in der Messung beobachtet).
    lizenz_id, lizenz_roh = "", []
    for tag in roh.get("tags") or []:
        if isinstance(tag, str) and tag.startswith("license:"):
            lizenz_roh.append({"tag": tag})
            if not lizenz_id:
                lizenz_id = tag.split("license:", 1)[1]
    card_lizenz = (roh.get("cardData") or {}).get("license")
    if card_lizenz:
        lizenz_roh.append({"cardData.license": card_lizenz})
        if not lizenz_id:
            if isinstance(card_lizenz, list) and card_lizenz:
                lizenz_id = _text(card_lizenz[0])
            elif isinstance(card_lizenz, str):
                lizenz_id = _text(card_lizenz)

    # Zugangsstufe aus `gated` (Design-Vokabular open/registration/request):
    # False  → open (keine Freigabe nötig)
    # "auto" → registration (automatisierte Zustimmung/Klick-Through, keine
    #          menschliche Prüfung — näher an Selbstregistrierung als an Anfrage)
    # "manual" → request (menschliche Prüfung vor Freigabe, kann abgelehnt werden)
    gated = roh.get("gated")
    if gated in (False, None, "false", ""):
        stufe = "open"
    elif gated == "auto":
        stufe = "registration"
    elif gated == "manual":
        stufe = "request"
    else:
        stufe = ""  # unbekannter gated-Wert — nicht raten

    konstruierte_url = f"https://huggingface.co/datasets/{hf_id}" if hf_id else ""

    aktualisiert = _text(roh.get("lastModified"))
    daten = [{"datum": aktualisiert, "typ": "lastModified"}] if aktualisiert else []

    identifikatoren = [{"schema": "huggingface-id", "wert": hf_id}] if hf_id else []

    # disabled/private sind HuggingFace-Zustände mit derselben Bedeutung wie
    # DataCites nicht-"findable"-Stati — in schranken.ZURUECKGEZOGENE_STATI
    # aufgenommen statt eines eigenen Sonderfalls.
    quell_status = ""
    if roh.get("disabled"):
        quell_status = "disabled"
    elif roh.get("private"):
        quell_status = "private"

    return {
        "id": hub_id("huggingface-id", hf_id) if hf_id
              else hub_id(fund.get("quelle", ""), fund.get("quell_id", "")),
        "granularitaet": "dataset" if hf_id else "",
        "titel": titel,
        "beschreibung": beschreibung,
        "urheber": urheber,
        "herausgeber": "",
        "publikationsjahr": None,
        "daten": daten,
        "raeumlichkeit": [],
        "lizenz": {"id": lizenz_id, "roh": lizenz_roh},
        "zugang": {"stufe": stufe, "url": konstruierte_url, "geprueft": "none",
                   "geprueft_am": "", "http_status": None, "finale_url": "",
                   "url_konstruiert": bool(konstruierte_url)},
        "identifikatoren": identifikatoren,
        "relationen": [],
        "quell_status": quell_status,
        "status": "ungeprueft",
        "fundstellen": [{"quelle": fund.get("quelle"), "quell_id": fund.get("quell_id"),
                         "geerntet": fund.get("geerntet"),
                         "adapter_version": fund.get("adapter_version")}],
    }


NORMALISIERER = {
    "datacite": normalisiere_datacite,
    "kaggle": normalisiere_kaggle,
    "arcgis": normalisiere_arcgis,
    "huggingface": normalisiere_huggingface,
}
