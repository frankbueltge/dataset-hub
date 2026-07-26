"""Tests für den HuggingFace-Adapter: Normalisierung, Zugangsstufen-Zuordnung und
vor allem die Quellen-Ausnahme (konstruierte URL) samt ihrer harten Durchsetzung
in schranken.py — offline, kein Netz."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from hub_lib import hub_id  # noqa: E402
from normalisiere import normalisiere_huggingface  # noqa: E402
from schranken import pruefe  # noqa: E402


def fundstelle(hf_id="orga/testdatensatz", **roh_extra):
    roh = {
        "id": hf_id,
        "author": "orga",
        "cardData": {"pretty_name": "Testdatensatz HF", "license": ["mit"]},
        "description": "Ein Testdatensatz.",
        "tags": ["license:mit", "task_categories:text-generation"],
        "gated": False,
        "disabled": False,
        "private": False,
        "lastModified": "2026-07-26T10:00:00.000Z",
    }
    roh.update(roh_extra)
    return {"quelle": "huggingface", "quell_id": hf_id, "geerntet": "2026-07-26T12:00:00Z",
            "adapter_version": "0.1.0", "roh": roh}


class TestNormalisierungHuggingface(unittest.TestCase):
    def test_kernfelder(self):
        e = normalisiere_huggingface(fundstelle())
        self.assertEqual(e["titel"], "Testdatensatz HF")
        self.assertEqual(e["urheber"], [{"name": "orga"}])
        self.assertEqual(e["beschreibung"], "Ein Testdatensatz.")
        self.assertEqual(e["lizenz"]["id"], "mit")
        self.assertEqual(e["zugang"]["stufe"], "open")
        self.assertEqual(e["id"], hub_id("huggingface-id", "orga/testdatensatz"))

    def test_konstruierte_url_folgt_dokumentiertem_api_vertrag(self):
        e = normalisiere_huggingface(fundstelle())
        self.assertEqual(e["zugang"]["url"],
                         "https://huggingface.co/datasets/orga/testdatensatz")
        self.assertTrue(e["zugang"]["url_konstruiert"])
        self.assertEqual(e["zugang"]["geprueft"], "none")  # Anfangszustand, ungeprüft

    def test_titel_faellt_auf_id_zurueck_ohne_pretty_name(self):
        # id ist ein wörtliches Quellfeld (100 % Abdeckung) -- kein erfundener Titel.
        e = normalisiere_huggingface(fundstelle(cardData={}))
        self.assertEqual(e["titel"], "orga/testdatensatz")

    def test_autor_faellt_auf_namensraum_zurueck_ohne_author_feld(self):
        e = normalisiere_huggingface(fundstelle(author=""))
        self.assertEqual(e["urheber"], [{"name": "orga"}])

    def test_lizenz_aus_tag_ohne_carddata(self):
        e = normalisiere_huggingface(fundstelle(cardData={}, tags=["license:apache-2.0"]))
        self.assertEqual(e["lizenz"]["id"], "apache-2.0")

    def test_lizenz_carddata_als_string_statt_liste(self):
        e = normalisiere_huggingface(fundstelle(tags=[], cardData={"license": "apache-2.0"}))
        self.assertEqual(e["lizenz"]["id"], "apache-2.0")

    def test_gated_auto_wird_registration(self):
        e = normalisiere_huggingface(fundstelle(gated="auto"))
        self.assertEqual(e["zugang"]["stufe"], "registration")

    def test_gated_manual_wird_request(self):
        e = normalisiere_huggingface(fundstelle(gated="manual"))
        self.assertEqual(e["zugang"]["stufe"], "request")

    def test_disabled_setzt_quell_status(self):
        e = normalisiere_huggingface(fundstelle(disabled=True))
        self.assertEqual(e["quell_status"], "disabled")

    def test_fehlendes_bleibt_leer(self):
        e = normalisiere_huggingface(fundstelle(description="", tags=[], cardData={}))
        self.assertEqual(e["beschreibung"], "")
        self.assertEqual(e["lizenz"], {"id": "", "roh": []})


class TestSchrankenHuggingfaceKonstruierteUrl(unittest.TestCase):
    """Kern der Auflage (schema/SCHEMA.md, Quellen-Ausnahme): kein Eintrag mit
    konstruierter URL darf ohne bestätigte HTTP-Auflösung in den Bestand."""

    def test_unaufgeloester_hf_eintrag_wird_abgelehnt(self):
        e = normalisiere_huggingface(fundstelle())
        self.assertEqual(e["zugang"]["geprueft"], "none")
        self.assertEqual(pruefe(e), "konstruierte-url-ungeprueft")

    def test_nur_versucht_aber_nicht_bestaetigt_wird_ebenfalls_abgelehnt(self):
        # 'versucht' heißt: aufgelöst, aber der Host antwortete nicht mit 2xx
        # (z. B. HTTP 403) -- das ist kein Beweis für Erreichbarkeit.
        e = normalisiere_huggingface(fundstelle())
        e["zugang"]["geprueft"] = "versucht"
        self.assertEqual(pruefe(e), "konstruierte-url-ungeprueft")

    def test_bestaetigt_aufgeloester_hf_eintrag_passiert(self):
        e = normalisiere_huggingface(fundstelle())
        e["zugang"]["geprueft"] = "landing"
        self.assertIsNone(pruefe(e))

    def test_download_gilt_ebenfalls_als_bestaetigt(self):
        e = normalisiere_huggingface(fundstelle())
        e["zugang"]["geprueft"] = "download"
        self.assertIsNone(pruefe(e))

    def test_quelle_ohne_konstruierte_url_ist_von_der_auflage_unberuehrt(self):
        # Gegenprobe: eine Quelle mit wörtlicher URL (kein url_konstruiert-Merkmal)
        # darf nicht durch diese Auflage blockiert werden.
        from normalisiere import normalisiere_kaggle
        roh = {"ref": "x/y", "title": "T", "creatorName": "A",
               "url": "https://www.kaggle.com/datasets/x/y"}
        fund = {"quelle": "kaggle", "quell_id": "x/y", "geerntet": "2026-07-26T12:00:00Z",
                "adapter_version": "0.1.0", "roh": roh}
        e = normalisiere_kaggle(fund)
        self.assertNotIn("url_konstruiert", e["zugang"])
        self.assertIsNone(pruefe(e))


if __name__ == "__main__":
    unittest.main()
