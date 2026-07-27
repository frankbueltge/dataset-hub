"""Offline-Tests des Steinbruch-Abbaus (Neufassung §5) und der Normalisierung
gegen fehlerhafte Quelldaten. Keine Netz- und keine Dateiabhängigkeit."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from hole_aus_steinbruch import _knapper_eintrag  # noqa: E402
from normalisiere import normalisiere_datacite  # noqa: E402
from relevanz import Massenherausgeber, lizenz_benannt  # noqa: E402

MASSEN = Massenherausgeber({"PISCO MN": {"name": "PISCO MN"}})


def fund(**roh_extra):
    roh = {
        "doi": "10.5555/test.1",
        "titles": [{"title": "Testdatensatz"}],
        "creators": [{"name": "Muster, Erika"}],
        "publisher": "Testarchiv",
        "url": "https://example.org/1",
        "types": {"resourceTypeGeneral": "Dataset"},
        "rightsList": [{"rightsIdentifier": "cc-by-4.0"}],
        "state": "findable",
    }
    roh.update(roh_extra)
    return {"quelle": "datacite", "quell_id": "10.5555/test.1",
            "geerntet": "2026-07-27T00:00:00Z", "roh": roh}


class TestNormalisierungGegenFehlerhafteQuellen(unittest.TestCase):
    """Regression: der Bulk-Abbau stürzte auf Teil 33 des DataCite Public Data File ab,
    weil ein `nameIdentifiers`-Eintrag eine Zeichenkette statt eines Objekts war."""

    def test_nameidentifiers_als_zeichenkette_stuerzt_nicht(self):
        e = normalisiere_datacite(fund(creators=[
            {"name": "Muster, Erika", "nameIdentifiers": ["https://orcid.org/0000-0001"]}]))
        self.assertEqual(e["urheber"], [{"name": "Muster, Erika"}])

    def test_zeichenkette_wird_uebersprungen_nicht_gedeutet(self):
        # Aus 'ORCID-irgendwas' einen Identifikator zu raten hieße erfinden.
        e = normalisiere_datacite(fund(creators=[
            {"name": "Muster, Erika",
             "nameIdentifiers": ["0000-0002-1825-0097",
                                 {"nameIdentifierScheme": "ORCID",
                                  "nameIdentifier": "0000-0003-1111-2222"}]}]))
        self.assertEqual(e["urheber"][0].get("orcid"), "0000-0003-1111-2222")

    def test_alle_quellenlisten_vertragen_zeichenketten(self):
        e = normalisiere_datacite(fund(
            titles=["nur ein String", {"title": "Echter Titel"}],
            descriptions=["String", {"description": "Echte Beschreibung"}],
            rightsList=["String", {"rightsIdentifier": "cc0-1.0"}],
            dates=["String", {"date": "2026-01-01", "dateType": "Issued"}],
            alternateIdentifiers=["String", {"alternateIdentifier": "abc",
                                             "alternateIdentifierType": "Handle"}],
            relatedIdentifiers=["String", {"relatedIdentifier": "10.5555/x",
                                           "relatedIdentifierType": "DOI",
                                           "relationType": "IsVersionOf"}]))
        self.assertEqual(e["titel"], "Echter Titel")
        self.assertEqual(e["beschreibung"], "Echte Beschreibung")
        self.assertEqual(e["lizenz"]["id"], "cc0-1.0")
        self.assertEqual(e["daten"], [{"datum": "2026-01-01", "typ": "Issued"}])
        self.assertEqual(len(e["identifikatoren"]), 2)
        self.assertEqual(len(e["relationen"]), 1)


class TestKnapperEintrag(unittest.TestCase):
    """Der Abbau prüft Stufe 1 auf dem Rohdatensatz, um 97 % der Bulk-Zeilen nicht
    erst vollständig zu normalisieren. Die Abkürzung muss dieselben Urteile fällen
    wie der volle Weg — sonst wäre sie ein zweites, stilles Kriterium."""

    def _gleich(self, f):
        knapp, voll = _knapper_eintrag(f["roh"]), normalisiere_datacite(f)
        self.assertEqual(MASSEN.trifft(knapp), MASSEN.trifft(voll))
        self.assertEqual(lizenz_benannt(knapp), lizenz_benannt(voll))

    def test_gewoehnlicher_eintrag(self):
        self._gleich(fund())

    def test_herausgeber_als_objekt(self):
        self._gleich(fund(publisher={"name": "PISCO MN"}))

    def test_massenherausgeber_als_sammlung(self):
        f = fund(publisher="PISCO MN", types={"resourceTypeGeneral": "Collection"})
        self._gleich(f)
        self.assertFalse(MASSEN.trifft(_knapper_eintrag(f["roh"])))

    def test_massenherausgeber_als_einzelstueck(self):
        f = fund(publisher="PISCO MN")
        self._gleich(f)
        self.assertTrue(MASSEN.trifft(_knapper_eintrag(f["roh"])))

    def test_ohne_lizenz(self):
        self._gleich(fund(rightsList=[]))

    def test_lizenz_ohne_identifier(self):
        self._gleich(fund(rightsList=[{"rights": "Some custom terms"}]))

    def test_fehlender_typ(self):
        self._gleich(fund(types={}))

    def test_leerer_rohdatensatz(self):
        self._gleich({"quelle": "datacite", "quell_id": "x", "roh": {}})


if __name__ == "__main__":
    unittest.main()
