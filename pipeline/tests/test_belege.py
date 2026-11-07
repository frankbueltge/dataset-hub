"""Offline-Tests der Belegabfrage (belege.py). Kein Netzzugriff: der Abruf wird ersetzt."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import belege  # noqa: E402


class TestBelege(unittest.TestCase):
    def test_seitentitel_aus_html_und_json(self):
        self.assertEqual(belege.seitentitel("<html><title> Butterfly &amp; Moth </title>", "text/html"),
                         "Butterfly & Moth")
        self.assertEqual(belege.seitentitel('{"name": "Street Lights"}', "application/json"),
                         "Street Lights")
        self.assertIsNone(belege.seitentitel("kein json", "application/json"))

    def test_titelabgleich_ignoriert_akzente_und_satzzeichen(self):
        self.assertTrue(belege.kommt_vor("Kāniṭ Museum 3", "<h1>KANIT  museum-3</h1>"))
        self.assertFalse(belege.kommt_vor("Crotalaria pallida", "<div id=app></div>"))
        self.assertIsNone(belege.kommt_vor("", "irgendwas"))

    def test_abgeleitete_api_nur_fuer_bekannte_quellen(self):
        self.assertEqual(
            belege.abgeleitete_api("https://www.gbif.org/dataset/edd9b710-f3bb-4c49-9fa5-724cd4ecfc7d"),
            "https://api.gbif.org/v1/dataset/edd9b710-f3bb-4c49-9fa5-724cd4ecfc7d")
        self.assertEqual(
            belege.abgeleitete_api("https://www.gbif.org/occurrence/download/0008659-260721160103020"),
            "https://api.gbif.org/v1/occurrence/download/0008659-260721160103020")
        self.assertEqual(
            belege.abgeleitete_api("https://s.arcgis.com/x/arcgis/rest/services/A/FeatureServer/7"),
            "https://s.arcgis.com/x/arcgis/rest/services/A/FeatureServer/7?f=json")
        self.assertIsNone(belege.abgeleitete_api("https://dasi.cnr.it/epigraphs/9783"))

    def test_sammle_ohne_doppelte_und_ohne_leere_urls(self):
        e1 = {"id": "dh-1", "titel": "A", "url": "https://a.example/1"}
        e2 = {"id": "dh-2", "titel": "A", "url": ""}
        aufgaben = belege.sammle([{"eintraege": [e1, e2]}], [e1])
        self.assertEqual([a["id"] for a in aufgaben], ["dh-1"])

    def test_ausfall_wird_vermerkt_nicht_ueberbrueckt(self):
        def faellt_aus(url, **_):
            raise RuntimeError("AUSFALL nach 2 Versuchen")
        b = belege.Abrufer(drossel=0, holen=faellt_aus)("https://a.example/1", "A")
        self.assertIsNone(b["status"])
        self.assertIn("AUSFALL", b["ausfall"])

    def test_pruefe_haengt_api_beleg_an(self):
        def holen(url, **_):
            if "api.gbif.org" in url:
                return 200, b'{"title": "Herbarium X"}', {"content-type": "application/json"}, url
            return 200, b"<div id=app></div>", {"content-type": "text/html"}, url
        url = "https://www.gbif.org/dataset/edd9b710-f3bb-4c49-9fa5-724cd4ecfc7d"
        [b] = belege.pruefe([{"id": "dh-1", "titel": "Herbarium X", "url": url}],
                            belege.Abrufer(drossel=0, holen=holen))
        self.assertFalse(b["titel_im_text"])
        self.assertTrue(b["api"]["abgeleitet"])
        self.assertTrue(b["api"]["titel_im_text"])
        self.assertEqual(b["api"]["seitentitel"], "Herbarium X")


if __name__ == "__main__":
    unittest.main()
