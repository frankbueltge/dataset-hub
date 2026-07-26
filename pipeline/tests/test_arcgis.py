"""Tests für den ArcGIS-Hub-Adapter: Normalisierung, Dedup-Wahl, Schranken
(offline, kein Netz)."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from hub_lib import hub_id  # noqa: E402
from normalisiere import normalisiere_arcgis  # noqa: E402
from schranken import pruefe  # noqa: E402


def fundstelle(layer_id="itemabc123_0", item_id="itemabc123", **attr_extra):
    attr = {
        "name": "Testdatensatz ArcGIS",
        "owner": "TestOrgUser",
        "orgName": "Test Org",
        "organization": "Test Org",
        "source": "Test Org",
        "url": "https://services.arcgis.com/test/FeatureServer/0",
        "type": "Feature Layer",
        "modified": 1785060048137,
        "license": "CC0-1.0",
        "structuredLicense": {"name": "Public Domain Dedication", "type": "CC0-1.0",
                              "abbr": "CC0"},
        "extent": {"coordinates": [[-1, -1], [1, 1]], "type": "envelope"},
        "itemId": item_id,
    }
    attr.update(attr_extra)
    roh = {
        "id": layer_id, "type": "dataset", "attributes": attr,
        "links": {"itemPage": f"https://www.arcgis.com/home/item.html?id={item_id}"},
    }
    return {"quelle": "arcgis", "quell_id": item_id, "geerntet": "2026-07-26T12:00:00Z",
            "adapter_version": "0.1.0", "roh": roh}


class TestNormalisierungArcgis(unittest.TestCase):
    def test_kernfelder(self):
        e = normalisiere_arcgis(fundstelle())
        self.assertEqual(e["titel"], "Testdatensatz ArcGIS")
        self.assertEqual(e["urheber"], [{"name": "TestOrgUser"}])
        self.assertEqual(e["herausgeber"], "Test Org")
        self.assertEqual(e["zugang"]["url"], "https://services.arcgis.com/test/FeatureServer/0")
        self.assertEqual(e["zugang"]["landingpage"],
                         "https://www.arcgis.com/home/item.html?id=itemabc123")
        self.assertEqual(e["granularitaet"], "service")
        self.assertEqual(e["lizenz"]["id"], "CC0-1.0")
        # id basiert auf itemId, NICHT auf dem Layer-spezifischen id-Feld
        self.assertEqual(e["id"], hub_id("arcgis-item", "itemabc123"))

    def test_dedup_quelle_ist_itemid_nicht_layer_id(self):
        """Kern der Auflage: quell_id (und damit die Fundstellen-Zusammenführung
        in baue_bestand.py) hängt an itemId, nicht am Layer-`id`-Feld — sonst
        zählte ein Multi-Layer-Service mehrfach im Hub."""
        a = fundstelle(layer_id="itemabc123_0", item_id="itemabc123")
        b = fundstelle(layer_id="itemabc123_1", item_id="itemabc123")
        ea, eb = normalisiere_arcgis(a), normalisiere_arcgis(b)
        self.assertEqual(ea["id"], eb["id"])
        # der Layer-spezifische id bleibt als Zusatz-Identifikator erhalten,
        # geht also nicht spurlos unter
        self.assertIn({"schema": "arcgis-layer-id", "wert": "itemabc123_0"},
                     ea["identifikatoren"])
        self.assertIn({"schema": "arcgis-layer-id", "wert": "itemabc123_1"},
                     eb["identifikatoren"])

    def test_unbekannter_typ_bleibt_ungeraten(self):
        e = normalisiere_arcgis(fundstelle(type="CSV Collection"))
        self.assertEqual(e["granularitaet"], "")

    def test_fehlendes_bleibt_leer(self):
        e = normalisiere_arcgis(fundstelle(extent=None, structuredLicense=None, license=None))
        self.assertEqual(e["raeumlichkeit"], [])
        self.assertEqual(e["lizenz"], {"id": "", "roh": []})


class TestSchrankenArcgis(unittest.TestCase):
    def test_vollstaendiger_eintrag_passiert(self):
        self.assertIsNone(pruefe(normalisiere_arcgis(fundstelle())))

    def test_ohne_url_abgelehnt(self):
        e = normalisiere_arcgis(fundstelle(url=""))
        self.assertEqual(pruefe(e), "keine-zugangs-url")

    def test_ohne_urheber_und_herausgeber_abgelehnt(self):
        e = normalisiere_arcgis(fundstelle(owner="", orgName="", organization="", source=""))
        self.assertEqual(pruefe(e), "kein-urheber-oder-herausgeber")


if __name__ == "__main__":
    unittest.main()
