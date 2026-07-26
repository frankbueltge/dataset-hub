"""Tests für den Kaggle-Adapter: Normalisierung + Schranken (offline, kein Netz)."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from hub_lib import hub_id  # noqa: E402
from normalisiere import normalisiere_kaggle  # noqa: E402
from schranken import pruefe  # noqa: E402


def fundstelle(ref="test-owner/test-dataset", **roh_extra):
    roh = {
        "ref": ref,
        "title": "Testdatensatz Kaggle",
        "subtitle": "Kurzbeschreibung",
        "creatorName": "Test Creator",
        "ownerName": "test-owner",
        "url": "https://www.kaggle.com/datasets/test-owner/test-dataset",
        "licenseName": "CC0: Public Domain",
        "totalBytes": 12345,
        "lastUpdated": "2026-07-26T10:00:00.000Z",
    }
    roh.update(roh_extra)
    return {"quelle": "kaggle", "quell_id": ref, "geerntet": "2026-07-26T12:00:00Z",
            "adapter_version": "0.1.0", "roh": roh}


class TestNormalisierungKaggle(unittest.TestCase):
    def test_kernfelder(self):
        e = normalisiere_kaggle(fundstelle())
        self.assertEqual(e["titel"], "Testdatensatz Kaggle")
        self.assertEqual(e["beschreibung"], "Kurzbeschreibung")
        self.assertEqual(e["urheber"], [{"name": "Test Creator"}])
        self.assertEqual(e["zugang"]["url"],
                         "https://www.kaggle.com/datasets/test-owner/test-dataset")
        self.assertEqual(e["status"], "ungeprueft")
        self.assertEqual(e["id"], hub_id("kaggle-ref", "test-owner/test-dataset"))
        self.assertEqual(e["identifikatoren"],
                         [{"schema": "kaggle-ref", "wert": "test-owner/test-dataset"}])

    def test_ownername_faellt_zurueck_ohne_creatorname(self):
        e = normalisiere_kaggle(fundstelle(creatorName=""))
        self.assertEqual(e["urheber"], [{"name": "test-owner"}])

    def test_lizenzname_bleibt_freitext_kein_erfundener_identifier(self):
        e = normalisiere_kaggle(fundstelle())
        # licenseName ist ein Freitextlabel, kein formaler Identifier — id bleibt
        # leer, der Wortlaut steht nur in roh (nichts erfinden).
        self.assertEqual(e["lizenz"]["id"], "")
        self.assertEqual(e["lizenz"]["roh"], [{"licenseName": "CC0: Public Domain"}])

    def test_fehlendes_bleibt_leer(self):
        e = normalisiere_kaggle(fundstelle(subtitle="", description="", licenseName=""))
        self.assertEqual(e["beschreibung"], "")
        self.assertEqual(e["lizenz"], {"id": "", "roh": []})


class TestSchrankenKaggle(unittest.TestCase):
    """Prüft die generischen Schranken am Kaggle-Beispiel.

    Die rechtliche Rückhaltung der Quelle (QUELLEN_ZURUECKGEHALTEN, 2026-07-26) greift
    vor allen inhaltlichen Schranken und würde jeden Fall gleich ablehnen. Sie wird
    hier gezielt ausgesetzt — die Rückhaltung selbst hat einen eigenen Test unten.
    """

    def setUp(self):
        import schranken
        self._gehalten = dict(schranken.QUELLEN_ZURUECKGEHALTEN)
        schranken.QUELLEN_ZURUECKGEHALTEN.pop('kaggle', None)

    def tearDown(self):
        import schranken
        schranken.QUELLEN_ZURUECKGEHALTEN.clear()
        schranken.QUELLEN_ZURUECKGEHALTEN.update(self._gehalten)

    def test_vollstaendiger_eintrag_passiert(self):
        self.assertIsNone(pruefe(normalisiere_kaggle(fundstelle())))

    def test_ohne_url_abgelehnt(self):
        e = normalisiere_kaggle(fundstelle(url=""))
        self.assertEqual(pruefe(e), "keine-zugangs-url")

    def test_ohne_titel_abgelehnt(self):
        e = normalisiere_kaggle(fundstelle(title=""))
        self.assertEqual(pruefe(e), "kein-titel")

    def test_ohne_urheber_abgelehnt(self):
        e = normalisiere_kaggle(fundstelle(creatorName="", ownerName=""))
        self.assertEqual(pruefe(e), "kein-urheber-oder-herausgeber")


if __name__ == "__main__":
    unittest.main()


class TestRechtlicheRueckhaltung(unittest.TestCase):
    """Gate G5: eine Quelle mit ungeklärter Rechtslage erscheint nicht im Bestand.

    Kaggles Nutzungsbedingungen untersagen, „any significant portion of the Content"
    zu speichern (messungen/register.md, Abschnitt Rechtliche Grundlage). Bis das
    geklärt ist, wird nichts von dort aufgenommen — die Rohernte bleibt im Archiv.
    """

    def test_kaggle_wird_zurueckgehalten(self):
        import schranken
        self.assertIn('kaggle', schranken.QUELLEN_ZURUECKGEHALTEN)
        e = normalisiere_kaggle(fundstelle())
        self.assertEqual(pruefe(e), 'quelle-rechtlich-ungeklaert')

    def test_rueckhaltung_greift_vor_inhaltlichen_schranken(self):
        """Auch ein sonst makelloser Eintrag bleibt draußen — und ein sonst
        fehlerhafter wird mit dem RECHTLICHEN Grund abgelehnt, nicht mit dem
        inhaltlichen: der Grundcode im Register muss den wahren Anlass nennen."""
        e = normalisiere_kaggle(fundstelle(title=''))
        self.assertEqual(pruefe(e), 'quelle-rechtlich-ungeklaert')
