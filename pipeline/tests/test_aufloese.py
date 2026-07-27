"""Offline-Tests der Drossel je Host (Neufassung, Prüfstand). Kein Netzzugriff:
robots.txt wird abgeschaltet, Zeit wird gemessen statt abgewartet."""
import pathlib
import sys
import time
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from aufloese import RUECKZUG_STATI, Hoeflichkeit  # noqa: E402


class TestDrosselJeHost(unittest.TestCase):
    def test_zweite_anfrage_an_denselben_host_wartet(self):
        h = Hoeflichkeit(0.25, robots_beachten=False)
        h.warte("zenodo.org")
        t0 = time.monotonic()
        h.warte("zenodo.org")
        self.assertGreaterEqual(time.monotonic() - t0, 0.2)

    def test_anderer_host_wartet_nicht(self):
        # Der ganze Sinn der Umstellung: 205 Hosts sollen nicht aufeinander warten.
        h = Hoeflichkeit(5.0, robots_beachten=False)
        h.warte("zenodo.org")
        t0 = time.monotonic()
        h.warte("figshare.com")
        self.assertLess(time.monotonic() - t0, 0.2)

    def test_stillgelegter_host_ist_vermerkt(self):
        h = Hoeflichkeit(0.0, robots_beachten=False)
        h.zurueckziehen("zenodo.org", "HTTP 429")
        self.assertIn("zenodo.org", h.stillgelegt)
        self.assertEqual(h.stillgelegt["zenodo.org"], "HTTP 429")

    def test_robots_abgeschaltet_erlaubt_alles(self):
        h = Hoeflichkeit(0.0, robots_beachten=False)
        self.assertTrue(h.darf("https://zenodo.org/records/1"))

    def test_rueckzugsstati_sind_die_hoeflichen(self):
        # 429 = zu viele Anfragen, 503 = überlastet. Beide heißen „weniger",
        # und auf beide wird nicht mit einem zweiten Versuch geantwortet.
        self.assertEqual(RUECKZUG_STATI, {429, 503})


class TestRobots(unittest.TestCase):
    def test_robots_regel_wird_angewandt(self):
        h = Hoeflichkeit(0.0, robots_beachten=True)
        # robots.txt-Abruf umgehen, indem der geparste Stand vorgegeben wird.
        import urllib.robotparser
        rp = urllib.robotparser.RobotFileParser()
        rp.parse(["User-agent: *", "Disallow: /privat/"])
        h._robots["example.org"] = rp
        self.assertFalse(h.darf("https://example.org/privat/x"))
        self.assertTrue(h.darf("https://example.org/offen/x"))

    def test_leeres_robots_erlaubt_alles(self):
        h = Hoeflichkeit(0.0, robots_beachten=True)
        import urllib.robotparser
        rp = urllib.robotparser.RobotFileParser()
        rp.parse([])
        h._robots["example.org"] = rp
        self.assertTrue(h.darf("https://example.org/irgendwas"))


if __name__ == "__main__":
    unittest.main()
