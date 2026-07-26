"""Normalisierung: Fundstelle → Eintrag (Schema v0.1). Fehlende Angaben bleiben leer."""
from hub_lib import hub_id, normalisiere_doi

GRANULARITAET = {"Dataset": "dataset", "Collection": "collection", "Service": "service"}


def _text(x) -> str:
    return x.strip() if isinstance(x, str) else ""


def normalisiere_datacite(fund: dict) -> dict:
    roh = fund.get("roh") or {}
    doi = normalisiere_doi(roh.get("doi") or fund.get("quell_id"))

    titel = ""
    for t in roh.get("titles") or []:
        titel = _text(t.get("title"))
        if titel:
            break

    beschreibung = ""
    for b in roh.get("descriptions") or []:
        beschreibung = _text(b.get("description"))
        if beschreibung:
            break

    urheber = []
    for c in roh.get("creators") or []:
        name = _text(c.get("name")) or " ".join(
            x for x in (_text(c.get("givenName")), _text(c.get("familyName"))) if x)
        if not name:
            continue
        orcid = ""
        for ni in c.get("nameIdentifiers") or []:
            if (ni.get("nameIdentifierScheme") or "").lower() == "orcid":
                orcid = _text(ni.get("nameIdentifier"))
        eintrag = {"name": name}
        if orcid:
            eintrag["orcid"] = orcid
        urheber.append(eintrag)

    pub = roh.get("publisher")
    herausgeber = _text(pub.get("name")) if isinstance(pub, dict) else _text(pub)

    lizenz_id, lizenz_roh = "", []
    for r in roh.get("rightsList") or []:
        lizenz_roh.append({k: v for k, v in r.items() if v})
        if not lizenz_id:
            lizenz_id = _text(r.get("rightsIdentifier"))

    daten = [{"datum": _text(d.get("date")), "typ": _text(d.get("dateType"))}
             for d in roh.get("dates") or [] if _text(d.get("date"))]

    identifikatoren = [{"schema": "doi", "wert": doi}] if doi else []
    for a in roh.get("alternateIdentifiers") or []:
        wert = _text(a.get("alternateIdentifier"))
        if wert:
            identifikatoren.append(
                {"schema": _text(a.get("alternateIdentifierType")).lower() or "unbekannt",
                 "wert": wert})

    relationen = []
    for rel in roh.get("relatedIdentifiers") or []:
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


NORMALISIERER = {"datacite": normalisiere_datacite}
