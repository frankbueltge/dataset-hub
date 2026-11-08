"""Offline-Test der Asset-Auswahl in kandidaten.py (Fehlauswahl seit dem 49. Lauf)."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from kandidaten import waehle_asset  # noqa: E402


class TestAssetAuswahl(unittest.TestCase):
    def test_nimmt_den_juengsten_bestand(self):
        assets = [{"name": "details.json.gz"}, {"name": "hub-2026-07-26.sqlite.gz"},
                  {"name": "hub-2026-07-27.sqlite.gz"}, {"name": "werke.json.gz"}]
        self.assertEqual(waehle_asset(assets)["name"], "hub-2026-07-27.sqlite.gz")

    def test_ohne_bestand_none(self):
        self.assertIsNone(waehle_asset([{"name": "meta.json.gz"}]))
        self.assertIsNone(waehle_asset([]))


if __name__ == "__main__":
    unittest.main()
