"""Offline-Tests der Pipeline-Kernlogik (unittest, keine Netzabhängigkeit)."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from dedupe import leite_gruppen_ab  # noqa: E402
from hub_lib import hub_id, normalisiere_doi  # noqa: E402
from normalisiere import normalisiere_datacite  # noqa: E402
from schranken import pruefe  # noqa: E402


def fundstelle(doi="10.5555/test.1", **roh_extra):
    roh = {
        "doi": doi,
        "titles": [{"title": "Testdatensatz"}],
        "creators": [{"name": "Muster, Erika",
                      "nameIdentifiers": [{"nameIdentifierScheme": "ORCID",
                                           "nameIdentifier": "0000-0000-0000-0001"}]}],
        "publisher": "Testarchiv",
        "publicationYear": 2026,
        "url": "https://example.org/datensatz/1",
        "types": {"resourceTypeGeneral": "Dataset"},
        "state": "findable",
    }
    roh.update(roh_extra)
    return {"quelle": "datacite", "quell_id": normalisiere_doi(doi),
            "geerntet": "2026-07-26T12:00:00Z", "adapter_version": "0.1.0", "roh": roh}


class TestNormalisierung(unittest.TestCase):
    def test_kernfelder(self):
        e = normalisiere_datacite(fundstelle())
        self.assertEqual(e["titel"], "Testdatensatz")
        self.assertEqual(e["urheber"], [{"name": "Muster, Erika",
                                         "orcid": "0000-0000-0000-0001"}])
        self.assertEqual(e["herausgeber"], "Testarchiv")
        self.assertEqual(e["zugang"]["url"], "https://example.org/datensatz/1")
        self.assertEqual(e["granularitaet"], "dataset")
        self.assertEqual(e["status"], "ungeprueft")
        self.assertEqual(e["id"], hub_id("doi", "10.5555/test.1"))

    def test_doi_normalisierung(self):
        self.assertEqual(normalisiere_doi("https://doi.org/10.5555/ABC"), "10.5555/abc")
        self.assertEqual(normalisiere_doi("doi:10.5555/x"), "10.5555/x")

    def test_fehlendes_bleibt_leer(self):
        e = normalisiere_datacite(fundstelle(rightsList=None, descriptions=None,
                                             geoLocations=None))
        self.assertEqual(e["lizenz"], {"id": "", "roh": []})
        self.assertEqual(e["beschreibung"], "")
        self.assertEqual(e["raeumlichkeit"], [])
        self.assertEqual(e["zugang"]["stufe"], "")  # unbekannt bleibt leer

    def test_publisher_als_objekt(self):
        e = normalisiere_datacite(fundstelle(publisher={"name": "Objekt-Verlag"}))
        self.assertEqual(e["herausgeber"], "Objekt-Verlag")


class TestSchranken(unittest.TestCase):
    def test_vollstaendiger_eintrag_passiert(self):
        self.assertIsNone(pruefe(normalisiere_datacite(fundstelle())))

    def test_ohne_titel_abgelehnt(self):
        e = normalisiere_datacite(fundstelle(titles=[]))
        self.assertEqual(pruefe(e), "kein-titel")

    def test_ohne_url_abgelehnt(self):
        e = normalisiere_datacite(fundstelle(url=""))
        self.assertEqual(pruefe(e), "keine-zugangs-url")

    def test_ohne_urheber_und_herausgeber_abgelehnt(self):
        e = normalisiere_datacite(fundstelle(creators=[], publisher=""))
        self.assertEqual(pruefe(e), "kein-urheber-oder-herausgeber")

    def test_nicht_oeffentlicher_status_abgelehnt(self):
        e = normalisiere_datacite(fundstelle(state="draft"))
        self.assertEqual(pruefe(e), "quellstatus-nicht-oeffentlich")


class TestAufloesungsStatus(unittest.TestCase):
    """'versucht' darf nie wie 'none' aussehen (Regel: Ausfälle vermerken, nie überbrücken)."""

    def test_enum_kennt_versucht(self):
        import json
        import pathlib
        schema = json.loads((pathlib.Path(__file__).resolve().parent.parent.parent
                             / "schema" / "eintrag.schema.json").read_text())
        werte = schema["properties"]["zugang"]["properties"]["geprueft"]["enum"]
        self.assertIn("versucht", werte)
        self.assertIn("none", werte)


class TestDedupe(unittest.TestCase):
    def _eintraege(self):
        a = normalisiere_datacite(fundstelle("10.5555/a"))
        b = normalisiere_datacite(fundstelle(
            "10.5555/b",
            relatedIdentifiers=[{"relationType": "IsVersionOf",
                                 "relatedIdentifierType": "DOI",
                                 "relatedIdentifier": "10.5555/a"}]))
        c = normalisiere_datacite(fundstelle("10.5555/c"))
        return {e["id"]: e for e in (a, b, c)}, a, b, c

    def test_r2_versionsrelation_gruppiert_werk_nicht_fassung(self):
        eintraege, a, b, c = self._eintraege()
        fassung, werk = leite_gruppen_ab(eintraege, {}, [])
        self.assertEqual(werk[a["id"]], werk[b["id"]])
        self.assertNotEqual(werk[a["id"]], werk[c["id"]])
        self.assertNotEqual(fassung[a["id"]], fassung[b["id"]])

    def test_r2_identitaet_gruppiert_fassung(self):
        eintraege, a, b, c = self._eintraege()
        b["relationen"] = [{"typ": "IsIdenticalTo", "ziel_schema": "DOI",
                            "ziel": "10.5555/a"}]
        fassung, werk = leite_gruppen_ab(eintraege, {}, [])
        self.assertEqual(fassung[a["id"]], fassung[b["id"]])

    def test_r3_gleiche_finale_url_nur_bei_echtem_pfad(self):
        eintraege, a, b, c = self._eintraege()
        b["relationen"] = []
        aufl = {a["id"]: {"ok": True, "finale_url": "https://ziel.org/ds/7"},
                c["id"]: {"ok": True, "finale_url": "https://ziel.org/ds/7"}}
        fassung, werk = leite_gruppen_ab(eintraege, aufl, [])
        self.assertEqual(fassung[a["id"]], fassung[c["id"]])
        # Wurzelpfad-Schutz: Catch-all-Redirects führen NICHT zusammen
        aufl_wurzel = {a["id"]: {"ok": True, "finale_url": "https://ziel.org/"},
                       c["id"]: {"ok": True, "finale_url": "https://ziel.org/"}}
        fassung2, _ = leite_gruppen_ab(eintraege, aufl_wurzel, [])
        self.assertNotEqual(fassung2[a["id"]], fassung2[c["id"]])

    def test_journal_merge_wird_angewendet(self):
        eintraege, a, b, c = self._eintraege()
        b["relationen"] = []
        journal = [{"typ": "merge", "ebene": "werk",
                    "mitglieder": [a["id"], c["id"]], "beleg": "Test", "quelle": "routine"}]
        _, werk = leite_gruppen_ab(eintraege, {}, journal)
        self.assertEqual(werk[a["id"]], werk[c["id"]])


if __name__ == "__main__":
    unittest.main()
