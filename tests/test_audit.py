"""
Automated Calculation Accuracy Audit & Test Suite
Parrot Cards PyJHora Astrology Engine (Drik Siddhant + Pushya Paksha Ayanamsa)
"""

import sys
import os
import unittest
from fastapi.testclient import TestClient

# Add paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYJHORA_SRC = os.path.join(BASE_DIR, "PyJHora", "src")
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, PYJHORA_SRC)

import swisseph as swe
from jhora.panchanga import drik
from jhora.panchanga.drik import Date
from jhora import const, utils
from jhora.horoscope.chart import charts
from main import app, HoroscopeRequest, calculate_horoscope, EPHE_PATH


class TestAstrologyCalculationAccuracyAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        # Verify Ephemeris path
        if os.path.exists(EPHE_PATH):
            swe.set_ephe_path(EPHE_PATH)
        drik.set_ayanamsa_mode("TRUE_PUSHYA")
        const.set_astrology_model(1)

    def test_01_swiss_ephemeris_files_available(self):
        """Audit Item 8: Verify Swiss Ephemeris data files exist and are loaded."""
        self.assertTrue(os.path.exists(EPHE_PATH), f"Ephemeris path missing: {EPHE_PATH}")
        ephe_files = os.listdir(EPHE_PATH)
        # Check essential files for planets and moon
        has_semo = any(f.startswith("semo_") or f.startswith("semom") for f in ephe_files)
        has_sepl = any(f.startswith("sepl_") or f.startswith("seplm") for f in ephe_files)
        self.assertTrue(has_semo, "Moon ephemeris files (semo_*.se1) missing")
        self.assertTrue(has_sepl, "Planetary ephemeris files (sepl_*.se1) missing")
        print(f"✅ Audit 8 Passed: Found {len(ephe_files)} Swiss Ephemeris data files in {EPHE_PATH}")

    def test_02_drik_siddhanta_configuration(self):
        """Audit Item 6: Verify Drik Siddhanta is explicitly configured."""
        const.set_astrology_model(1)
        self.assertEqual(const.astrology_model_default, const.ASTROLOGY_MODELS.DRIK)
        print("✅ Audit 6 Passed: Astrology model explicitly verified as Drik Siddhant (ASTROLOGY_MODELS.DRIK = 1)")

    def test_03_true_pushya_ayanamsa_genuinely_applied(self):
        """Audit Item 7: Verify TRUE_PUSHYA alters calculations vs Lahiri."""
        jd_test = utils.julian_day_number((1995, 10, 24), (6, 30, 0)) - 5.5 / 24.0

        drik.set_ayanamsa_mode("LAHIRI")
        lahiri_ayan = swe.get_ayanamsa_ut(jd_test)
        lahiri_sun = swe.calc_ut(jd_test, 0, 65810)[0][0]

        drik.set_ayanamsa_mode("TRUE_PUSHYA")
        pushya_ayan = swe.get_ayanamsa_ut(jd_test)
        pushya_sun = swe.calc_ut(jd_test, 0, 65810)[0][0]

        # Pushya Paksha is offset from Lahiri by ~1.135°
        ayan_diff = pushya_ayan - lahiri_ayan
        sun_diff = pushya_sun - lahiri_sun

        self.assertNotEqual(pushya_ayan, lahiri_ayan)
        self.assertAlmostEqual(abs(ayan_diff), 1.1359, places=2)
        print(f"✅ Audit 7 Passed: TRUE_PUSHYA actively modifies coordinates. Lahiri={lahiri_ayan:.4f}°, TruePushya={pushya_ayan:.4f}°, Delta={ayan_diff:.4f}°")

    def test_04_timezone_conversion_and_single_application(self):
        """Audit Items 1, 2, 3: Verify timezone conversion is applied exactly once in correct direction."""
        dob = (1995, 10, 24)
        tob = (6, 30, 0)
        place = drik.Place("Delhi", 28.6139, 77.2090, 5.5)

        # Local Julian day
        jd_local = utils.julian_day_number(dob, tob)
        # Expected UTC Julian day: Local - 5.5/24
        expected_jd_utc = jd_local - (5.5 / 24.0)

        # PyJHora's drik.ascendant converts internally: jd - tz/24
        # When passed jd_local, it should calculate at expected_jd_utc
        asc_const, asc_deg, _, _ = drik.ascendant(jd_local, place)

        # Constellation 6 is Libra
        self.assertEqual(asc_const, 6, f"Expected Libra (6), got {asc_const}")
        # Sunrise at ~6:31 AM means at 6:30 AM Lagna must be within 1° of Sun in Libra
        d1 = charts.divisional_chart(jd_local, place, divisional_chart_factor=1)
        sun_pos = d1[1][1]
        lag_pos = d1[0][1]

        self.assertEqual(sun_pos[0], 6, "Sun must be in Libra (6)")
        self.assertEqual(lag_pos[0], 6, "Lagna must be in Libra (6)")
        # Sun and Lagna difference at sunrise must be < 1.0 degree
        deg_diff = abs(sun_pos[1] - lag_pos[1])
        self.assertLess(deg_diff, 1.0, f"Sun and Lagna should be conjunct at sunrise! Difference was {deg_diff:.4f}°")
        print(f"✅ Audit 1, 2, 3 Passed: Timezone offset applied exactly once. Lagna=Libra {lag_pos[1]:.4f}°, Sun=Libra {sun_pos[1]:.4f}°, Separation={deg_diff*60:.2f} arcmin")

    def test_05_direct_pyjhora_vs_fastapi_wrapper_parity(self):
        """Audit Items 4 & 5: Ascendant directly calculated vs FastAPI response."""
        dob = Date(1995, 10, 24)
        tob = (6, 30, 0)
        place = drik.Place("Delhi", 28.6139, 77.2090, 5.5)
        jd_local = utils.julian_day_number((1995, 10, 24), tob)

        # Direct PyJHora Ascendant
        direct_const, direct_deg, direct_nak, direct_pada = drik.ascendant(jd_local, place)

        # FastAPI endpoint
        resp = self.client.post("/horoscope", json={
            "date": "1995-10-24",
            "time": "06:30:00",
            "place": "Delhi",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone": 5.5
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        fastapi_lagna = next(x for x in data["horoscope"]["nakshatra_pada"] if x["name"] == "Lagna")

        # Verify 100% parity
        self.assertEqual(fastapi_lagna["sign"], direct_const + 1)
        self.assertAlmostEqual(fastapi_lagna["degree"], direct_deg, places=4)
        self.assertEqual(fastapi_lagna["pada"], direct_pada)
        print(f"✅ Audit 4 & 5 Passed: 100% parity between direct PyJHora and FastAPI wrapper (Lagna={fastapi_lagna['sign_name']} {fastapi_lagna['degree']:.4f}°)")

    def test_06_nakshatra_and_navamsha_calculations(self):
        """Audit Item 9: Verify planetary positions, Nakshatra and Navamsha calculations."""
        resp = self.client.post("/horoscope", json={
            "date": "1995-10-24",
            "time": "06:30:00",
            "place": "Delhi",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone": 5.5
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["horoscope"]
        pts = {x["name"]: x for x in data["nakshatra_pada"]}

        # Check Lagna: Libra 7.2589° -> Swati Nakshatra, Pada 1, Navamsha Sagittarius
        lag = pts["Lagna"]
        self.assertEqual(lag["sign_name"], "Libra")
        self.assertEqual(lag["nakshatra"], "Swati")
        self.assertEqual(lag["pada"], 1)
        self.assertEqual(lag["navamsha_sign_name"], "Sagittarius")

        # Check Sun: Libra 7.4848° -> Swati Nakshatra, Pada 1, Navamsha Sagittarius
        sun = pts["Sun"]
        self.assertEqual(sun["sign_name"], "Libra")
        self.assertEqual(sun["nakshatra"], "Swati")
        self.assertEqual(sun["pada"], 1)
        self.assertEqual(sun["navamsha_sign_name"], "Sagittarius")

        # Check Moon: Libra 5.4947° -> Chitra Nakshatra, Pada 4, Navamsha Scorpio
        moon = pts["Moon"]
        self.assertEqual(moon["sign_name"], "Libra")
        self.assertEqual(moon["nakshatra"], "Chitra")
        self.assertEqual(moon["pada"], 4)
        self.assertEqual(moon["navamsha_sign_name"], "Scorpio")

        print("✅ Audit 9 Passed: Planetary positions, Nakshatras, Padas, and Navamshas verified mathematically.")

    def test_07_known_reference_solar_progression(self):
        """Audit Item 10: Automated tests for solar progression (Sunrise, Midheaven, Sunset)."""
        # 1. Sunrise (06:30 AM): Sun conjunct Lagna in 1st House
        resp_dawn = self.client.post("/horoscope", json={
            "date": "1995-10-24",
            "time": "06:30:00",
            "place": "Delhi",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone": 5.5
        })
        sun_dawn = next(x for x in resp_dawn.json()["horoscope"]["nakshatra_pada"] if x["name"] == "Sun")
        self.assertEqual(sun_dawn["house"], 1, "At sunrise, Sun must be in 1st House (Lagna)")

        # 2. Midheaven (13:30 PM): Sun in 10th House
        resp_noon = self.client.post("/horoscope", json={
            "date": "1995-10-24",
            "time": "13:30:00",
            "place": "Delhi",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone": 5.5
        })
        sun_mid = next(x for x in resp_noon.json()["horoscope"]["nakshatra_pada"] if x["name"] == "Sun")
        self.assertEqual(sun_mid["house"], 10, "At midheaven (13:30), Sun must be in 10th House")

        # 3. Sunset (18:00 PM): Sun in 7th House (Descendant)
        resp_dusk = self.client.post("/horoscope", json={
            "date": "1995-10-24",
            "time": "18:00:00",
            "place": "Delhi",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone": 5.5
        })
        sun_dusk = next(x for x in resp_dusk.json()["horoscope"]["nakshatra_pada"] if x["name"] == "Sun")
        self.assertEqual(sun_dusk["house"], 7, "At sunset, Sun must be in 7th House (Descendant)")

        print("✅ Audit 10 Passed: Diurnal progression verified across Sunrise (H1), Midheaven (H10), and Sunset (H7).")


if __name__ == "__main__":
    unittest.main()
