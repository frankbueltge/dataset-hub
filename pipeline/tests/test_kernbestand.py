"""Offline-Tests des Kernbestand-Merkmals (Neufassung §4, Stufe 2)."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from kernbestand import bestimme, siebe, urteile_aus_journal  # noqa: E402


def eintrag(titel="Irgendein Datensatz", beschreibung="", herausgeber="Testarchiv",
            eid="dh-test-1"):
    return {"id": eid, "titel": titel, "beschreibung": beschreibung,
            "herausgeber": herausgeber}


class TestSieb(unittest.TestCase):
    def test_sicherer_begriff_im_titel_ist_regel(self):
        stufe, treffer = siebe(eintrag(titel="Public procurement notices 2015–2024"))
        self.assertEqual(stufe, "regel")
        self.assertEqual(treffer[0]["feld"], "macht_verwaltung")
        self.assertEqual(treffer[0]["in"], "titel")

    def test_derselbe_begriff_nur_in_der_beschreibung_ist_grenzfall(self):
        # Der Kern der Präzisionsregel: der Titel sagt, was ein Datensatz IST,
        # die Beschreibung sagt nur, was er berührt.
        stufe, treffer = siebe(eintrag(
            titel="Spatio-temporal distribution of traffic accidents",
            beschreibung="Labels were produced with a large language model."))
        self.assertEqual(stufe, "grenzfall")
        self.assertEqual(treffer[0]["in"], "beschreibung")

    def test_epidemiologische_ueberwachung_wird_zurueckgestuft(self):
        # Gemessener Fehlgriff vom 27.07.: „surveillance" traf Vogelgrippe.
        stufe, treffer = siebe(eintrag(
            titel="Avian influenza surveillance in albatrosses",
            beschreibung="Sampling of pathogen prevalence in seabird colonies."))
        self.assertEqual(stufe, "grenzfall")
        self.assertEqual(treffer[0]["gegenbegriff"].lower(), "influenza")

    def test_staatliche_ueberwachung_bleibt_regel(self):
        stufe, _ = siebe(eintrag(titel="Anti-Surveillance Property Management Ledger"))
        self.assertEqual(stufe, "regel")

    def test_handschriften_census_wird_zurueckgestuft(self):
        stufe, treffer = siebe(eintrag(titel="Galen Digital-Coverage Census",
                                       beschreibung="Greek manuscript coverage."))
        self.assertEqual(stufe, "grenzfall")
        self.assertIn("gegenbegriff", treffer[0])

    def test_bevoelkerungszensus_bleibt_regel(self):
        stufe, _ = siebe(eintrag(
            titel="ABS 2021 Census G01 Selected person characteristics by sex"))
        self.assertEqual(stufe, "regel")

    def test_amtlicher_herausgeber_ist_grenzfall_nicht_regel(self):
        # Ein statistisches Amt veröffentlicht auch Geodaten und Verwaltungsinterna.
        stufe, treffer = siebe(eintrag(titel="Gemeindegrenzen 2024",
                                       herausgeber="Statistisches Bundesamt"))
        self.assertEqual(stufe, "grenzfall")
        self.assertEqual(treffer[0]["art"], "herausgeber")

    def test_weiter_begriff_ist_grenzfall(self):
        stufe, treffer = siebe(eintrag(titel="Regional Equity Index 2018"))
        self.assertEqual(stufe, "grenzfall")
        self.assertEqual(treffer[0]["art"], "weiter_begriff")

    def test_ohne_treffer_kein_kernbestand(self):
        stufe, treffer = siebe(eintrag(titel="Bodenfeuchte Messreihe Feld B3"))
        self.assertIsNone(stufe)
        self.assertEqual(treffer, [])

    def test_mehrere_felder_werden_alle_belegt(self):
        stufe, treffer = siebe(eintrag(
            titel="Predictive policing and public procurement in city budgets"))
        self.assertEqual(stufe, "regel")
        self.assertGreaterEqual(len({t["feld"] for t in treffer}), 2)


class TestUrteile(unittest.TestCase):
    def test_urteil_ueberstimmt_den_sieb(self):
        journal = [{"typ": "kein_kernbestand", "mitglieder": ["dh-a"],
                    "beleg": "Fachdatensatz ohne Bezug zur Ökologie."}]
        e = eintrag(titel="Public procurement notices", eid="dh-a")
        self.assertEqual(siebe(e)[0], "regel")
        im_kern, herkunft, _ = bestimme(e, urteile_aus_journal(journal))
        self.assertFalse(im_kern)
        self.assertEqual(herkunft, "urteil")

    def test_urteil_holt_grenzfall_herein(self):
        journal = [{"typ": "kernbestand", "mitglieder": ["dh-b"], "beleg": "…"}]
        e = eintrag(titel="Regional Equity Index 2018", eid="dh-b")
        im_kern, herkunft, _ = bestimme(e, urteile_aus_journal(journal))
        self.assertTrue(im_kern)
        self.assertEqual(herkunft, "urteil")

    def test_spaeteres_urteil_ueberstimmt_frueheres(self):
        journal = [{"typ": "kernbestand", "mitglieder": ["dh-c"]},
                   {"typ": "kein_kernbestand", "mitglieder": ["dh-c"]}]
        self.assertEqual(urteile_aus_journal(journal), {"dh-c": False})

    def test_unbeurteilter_grenzfall_bleibt_draussen(self):
        e = eintrag(titel="Regional Equity Index 2018", eid="dh-d")
        im_kern, herkunft, _ = bestimme(e, {})
        self.assertFalse(im_kern)
        self.assertEqual(herkunft, "grenzfall")

    def test_fremde_journal_typen_stoeren_nicht(self):
        journal = [{"typ": "merge", "ebene": "werk", "mitglieder": ["dh-e", "dh-f"]}]
        self.assertEqual(urteile_aus_journal(journal), {})


if __name__ == "__main__":
    unittest.main()
