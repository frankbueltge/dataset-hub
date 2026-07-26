"""Dedup-Stufen R1–R4 (Design §1.2) — deterministisch, keine Ähnlichkeits-Merges.

R1 steckt in der ID-Bildung (gleiche normalisierte PID → gleiche Eintrags-ID).
R2 nutzt nur quellen-behauptete Relationen. R3 nur tatsächlich aufgelöste URLs.
R4 ist ein Hook (DataCite deklariert keine Aggregatorkopien). Urteils-Merges kommen
als Journal-Ereignisse dazu; Rücknahme = Revert des Journals + Neubau.
"""
from urllib.parse import urlparse

from hub_lib import hub_id, normalisiere_doi

IDENTITAETS_RELATIONEN = {"IsIdenticalTo"}
VERSIONS_RELATIONEN = {"IsVersionOf", "HasVersion", "IsNewVersionOf", "IsPreviousVersionOf"}


class UnionFind:
    def __init__(self, elemente):
        self.eltern = {e: e for e in elemente}

    def finde(self, x):
        while self.eltern[x] != x:
            self.eltern[x] = self.eltern[self.eltern[x]]
            x = self.eltern[x]
        return x

    def vereine(self, a, b):
        ra, rb = self.finde(a), self.finde(b)
        if ra != rb:
            # deterministisch: kleinere ID wird Repräsentant
            if rb < ra:
                ra, rb = rb, ra
            self.eltern[rb] = ra

    def gruppen(self):
        return {e: self.finde(e) for e in self.eltern}


def _kein_wurzelpfad(url: str) -> bool:
    try:
        pfad = urlparse(url).path or ""
    except Exception:
        return False
    return pfad not in ("", "/")


def leite_gruppen_ab(eintraege: dict, aufloesungen: dict, journal: list):
    """eintraege: id → Eintrag. aufloesungen: id → {ok, finale_url}.
    journal: Liste von Ereignissen {typ:'merge', ebene:'werk'|'fassung', mitglieder:[...]}.
    Rückgabe: (fassung_von, werk_von) — id → Gruppen-Repräsentant."""
    ids = sorted(eintraege)
    fassung, werk = UnionFind(ids), UnionFind(ids)

    # R2 — quellen-behauptete Relationen (nur Ziele, die im Bestand existieren)
    for eid in ids:
        for rel in eintraege[eid].get("relationen") or []:
            if (rel.get("ziel_schema") or "").upper() != "DOI":
                continue
            ziel_id = hub_id("doi", normalisiere_doi(rel.get("ziel")))
            if ziel_id not in eintraege:
                continue
            typ = rel.get("typ")
            if typ in IDENTITAETS_RELATIONEN:
                fassung.vereine(eid, ziel_id)
                werk.vereine(eid, ziel_id)
            elif typ in VERSIONS_RELATIONEN:
                werk.vereine(eid, ziel_id)

    # R3 — identische finale URL nach tatsächlicher Auflösung (2xx, kein Wurzelpfad)
    nach_finaler_url = {}
    for eid in ids:
        a = aufloesungen.get(eid)
        if a and a.get("ok") and _kein_wurzelpfad(a.get("finale_url") or ""):
            nach_finaler_url.setdefault(a["finale_url"], []).append(eid)
    for gruppe in nach_finaler_url.values():
        for eid in gruppe[1:]:
            fassung.vereine(gruppe[0], eid)
            werk.vereine(gruppe[0], eid)

    # R4 — Aggregatorkopien: Hook; DataCite deklariert keine. Bewusst leer.

    # Journal-Ereignisse (Urteils-Merges) — nur 'merge'; Rücknahme via Git-Revert
    for ereignis in journal:
        if ereignis.get("typ") != "merge":
            continue
        mitglieder = [m for m in ereignis.get("mitglieder") or [] if m in eintraege]
        ziel_uf = werk if ereignis.get("ebene") == "werk" else fassung
        for m in mitglieder[1:]:
            ziel_uf.vereine(mitglieder[0], m)
            if ereignis.get("ebene") == "fassung":
                werk.vereine(mitglieder[0], m)

    return fassung.gruppen(), werk.gruppen()
