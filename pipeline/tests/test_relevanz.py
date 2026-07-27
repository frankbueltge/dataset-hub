"""Offline-Tests des Relevanzkriteriums (Neufassung §4). Keine Netzabhängigkeit."""
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from relevanz import (Massenherausgeber, lizenz_benannt, lizenz_offen,  # noqa: E402
                      pruefe_materialguete)


def eintrag(**extra):
    e = {"titel": "Testdatensatz", "herausgeber": "Testarchiv", "granularitaet": "dataset",
         "lizenz": {"id": "cc-by-4.0", "roh": []}}
    lizenz = extra.pop("lizenz_id", None)
    if lizenz is not None:
        e["lizenz"] = {"id": lizenz, "roh": []}
    e.update(extra)
    return e


MASSEN = Massenherausgeber({
    "National Institute for Fusion Science": {"name": "National Institute for Fusion Science"},
})


class TestLizenz(unittest.TestCase):
    def test_schreibweisen_derselben_lizenz(self):
        for schreibweise in ("cc-by-4.0", "CC-BY-4.0", "CC_BY_4_0", "CC BY 4.0"):
            with self.subTest(schreibweise=schreibweise):
                self.assertTrue(lizenz_offen(eintrag(lizenz_id=schreibweise)),
                                f"{schreibweise} sollte als offen gelten")

    def test_nc_und_nd_sind_nicht_offen(self):
        # Der wichtigste Fall: 'cc-by-nc-4.0' beginnt mit 'cc-by-' und rutschte durch,
        # wenn der Ausschluss nach dem Präfixvergleich stünde.
        for lizenz in ("cc-by-nc-4.0", "cc-by-nc-sa-3.0", "cc-by-nd-4.0", "CC-BY-NC-4.0"):
            with self.subTest(lizenz=lizenz):
                self.assertFalse(lizenz_offen(eintrag(lizenz_id=lizenz)))
                # …aber benannt sind sie sehr wohl, gehen also durch Stufe 1.
                self.assertTrue(lizenz_benannt(eintrag(lizenz_id=lizenz)))

    def test_platzhalter_gelten_nicht_als_benannt(self):
        for lizenz in ("", "custom", "none", "other", "unknown", "CUSTOM"):
            with self.subTest(lizenz=lizenz):
                self.assertFalse(lizenz_benannt(eintrag(lizenz_id=lizenz)))
                self.assertFalse(lizenz_offen(eintrag(lizenz_id=lizenz)))

    def test_cc0_und_odbl_sind_offen(self):
        for lizenz in ("cc0-1.0", "CC0-1.0", "ODbL-1.0", "ogl-uk-3.0"):
            with self.subTest(lizenz=lizenz):
                self.assertTrue(lizenz_offen(eintrag(lizenz_id=lizenz)))

    def test_versionsziffern_verschmelzen_nicht(self):
        # 'cc-by-40' ist kein Bezeichner der Quelle, sondern ein Tippfehler —
        # er darf nicht als 'cc-by-4.0' durchgehen.
        self.assertFalse(lizenz_offen(eintrag(lizenz_id="cc-by-40")))


class TestMassenherausgeber(unittest.TestCase):
    def test_einzelstueck_eines_massenherausgebers_faellt(self):
        e = eintrag(herausgeber="National Institute for Fusion Science")
        self.assertTrue(MASSEN.trifft(e))
        self.assertEqual(pruefe_materialguete(e, MASSEN), "massenregistrierung")

    def test_sammlung_desselben_herausgebers_bleibt(self):
        # Die Ausnahme aus §4: bezeichnet der Eintrag die Sammlung statt des
        # Einzelstücks, ist er genau das, was das Register will.
        e = eintrag(herausgeber="National Institute for Fusion Science",
                    granularitaet="collection")
        self.assertFalse(MASSEN.trifft(e))
        self.assertIsNone(pruefe_materialguete(e, MASSEN))

    def test_anderer_herausgeber_unberuehrt(self):
        self.assertIsNone(pruefe_materialguete(eintrag(), MASSEN))

    def test_fehlende_liste_bricht_ab_statt_still_durchzulassen(self):
        # Ohne Liste greift die Schranke nicht — das darf nie unbemerkt passieren.
        with self.assertRaises(FileNotFoundError):
            Massenherausgeber.lade(pathlib.Path("/gibt/es/nicht/massenherausgeber.json"))

    def test_liste_wird_aus_datei_gelesen(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "massenherausgeber.json"
            p.write_text(json.dumps({"herausgeber": [{"name": "PISCO MN", "n": 3984000}]}))
            m = Massenherausgeber.lade(p)
            self.assertTrue(m.trifft(eintrag(herausgeber="PISCO MN")))
            self.assertFalse(m.trifft(eintrag(herausgeber="Testarchiv")))


class TestMaterialguete(unittest.TestCase):
    def test_reihenfolge_massenregistrierung_vor_lizenz(self):
        # Ein Massen-Einzelstück ohne Lizenz soll als Massenregistrierung im Register
        # stehen, nicht als Lizenzmangel — sonst verschöbe sich die Statistik der
        # Ablehnungsgründe und die Ausmusterung wäre nicht mehr nachvollziehbar.
        e = eintrag(herausgeber="National Institute for Fusion Science", lizenz_id="")
        self.assertEqual(pruefe_materialguete(e, MASSEN), "massenregistrierung")

    def test_unbenannte_lizenz_faellt(self):
        self.assertEqual(pruefe_materialguete(eintrag(lizenz_id="custom"), MASSEN),
                         "lizenz-nicht-benannt")

    def test_nc_lizenz_passiert_stufe_eins(self):
        self.assertIsNone(pruefe_materialguete(eintrag(lizenz_id="cc-by-nc-4.0"), MASSEN))


if __name__ == "__main__":
    unittest.main()
