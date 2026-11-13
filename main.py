"""
Parrot Cards Astro Engine - FastAPI Microservice
Powered by PyJHora (Drik Siddhant + Pushya Paksha Ayanamsa)
"""

import sys
import os
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure PyJHora path is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYJHORA_SRC = os.path.join(BASE_DIR, "PyJHora", "src")
if PYJHORA_SRC not in sys.path:
    sys.path.insert(0, PYJHORA_SRC)

# Import PyJHora modules
try:
    import swisseph as swe
    from jhora.panchanga import drik
    from jhora.panchanga.drik import Date
    from jhora import const, utils
    from jhora.horoscope.chart import charts
except ImportError as e:
    raise ImportError(f"Failed to import PyJHora from {PYJHORA_SRC}: {e}")

# Configure Swiss Ephemeris data path
EPHE_PATH = os.path.join(PYJHORA_SRC, "jhora", "data", "ephe")
if os.path.exists(EPHE_PATH):
    swe.set_ephe_path(EPHE_PATH)

# Global configuration: Drik Siddhant + Pushya Paksha Ayanamsa
drik.set_ayanamsa_mode("TRUE_PUSHYA")
const.set_astrology_model(1)  # 1 = Drik Siddhant

app = FastAPI(
    title="Parrot Cards Cosmic Astro Engine",
    description="High-precision Vedic astrological calculation engine powered by PyJHora (Drik Siddhant & Pushya Paksha Ayanamsa).",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
]

SIGN_LORDS = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"
]

PLANET_NAMES = {
    0: "Sun",
    1: "Moon",
    2: "Mars",
    3: "Mercury",
    4: "Jupiter",
    5: "Venus",
    6: "Saturn",
    7: "Rahu",
    8: "Ketu",
}

SPECIAL_LAGNA_NAMES = {
    "BL": "Bhava Lagna",
    "HL": "Hora Lagna",
    "GL": "Ghati Lagna",
    "PL": "Pranapada Lagna",
    "VL": "Vighati Lagna",
    "KL": "Kunda Lagna",
    "BBL": "Bhrigu Bindhu Lagna",
    "SL": "Sree Lagna",
    "IL": "Indu Lagna",
}

UPAGRAHA_NAMES = {
    "Kl": "Kaala",
    "Mr": "Mrityu",
    "Ap": "Ardhaprahara",
    "Yg": "Yamaghantaka",
    "Gk": "Gulika",
    "Md": "Maandi",
    "Dm": "Dhuma",
    "Vp": "Vyatipata",
    "Pv": "Parivesha",
    "Ic": "Indra Chapa",
    "Uk": "Upaketu",
}

SPHUTA_NAMES = {
    "S1": "Tri Sphuta",
    "S2": "Chatur Sphuta",
    "S3": "Pancha Sphuta",
    "S4": "Prana Sphuta",
    "S5": "Deha Sphuta",
    "S6": "Mrityu Sphuta",
    "S7": "Sookshma Tri Sphuta",
    "S8": "Beeja Sphuta",
    "S9": "Kshetra Sphuta",
    "S10": "Tithi Sphuta",
    "S11": "Yoga Sphuta",
    "S12": "Rahu Tithi Sphuta",
    "S13": "Yogi Sphuta",
    "S14": "Avayogi Sphuta",
}

CHARA_KARAKA_CODES = {
    "atma_karaka": ("AK", "Atma Karaka"),
    "amatya_karaka": ("AmK", "Amatya Karaka"),
    "bhratri_karaka": ("BK", "Bhratri Karaka"),
    "matri_karaka": ("MK", "Matri Karaka"),
    "maitri_karaka": ("MK", "Matri Karaka"),
    "pitri_karaka": ("PiK", "Pitri Karaka"),
    "putra_karaka": ("PK", "Putra Karaka"),
    "gnati_karaka": ("GK", "Gnati Karaka"),
    "jnaati_karaka": ("GK", "Gnati Karaka"),
    "dara_karaka": ("DK", "Dara Karaka"),
    "data_karaka": ("DK", "Dara Karaka"),
}


class HoroscopeRequest(BaseModel):
    date: str = Field(..., description="Date of birth in YYYY-MM-DD format", example="1995-10-24")
    time: str = Field(..., description="Time of birth in HH:MM or HH:MM:SS format", example="06:30:00")
    place: Optional[str] = Field("Unknown", description="City / Location name", example="Delhi, India")
    latitude: float = Field(..., description="Latitude in decimal degrees", example=28.6139)
    longitude: float = Field(..., description="Longitude in decimal degrees", example=77.2090)
    timezone: float = Field(5.5, description="Timezone offset from UTC in hours", example=5.5)
    bhava_madhya_method: Optional[int] = Field(5, description="Bhava madhya method")


def make_point(name: str, rasi_index: int, deg_in_sign: float, lag_rasi: int) -> Dict[str, Any]:
    """Helper to construct standardized astronomical placement dict."""
    rasi_index = int(rasi_index) % 12
    deg_in_sign = float(deg_in_sign)
    abs_long = (rasi_index * 30.0 + deg_in_sign) % 360.0
    nak_idx = int(abs_long / (40.0 / 3.0)) % 27
    pada = int((abs_long % (40.0 / 3.0)) / (10.0 / 3.0)) + 1
    house = ((rasi_index - lag_rasi + 12) % 12) + 1
    sign_lord = SIGN_LORDS[rasi_index]
    nak_lord = NAKSHATRA_LORDS[nak_idx % 9]

    # Navamsha calculation: 1 Navamsha = 3° 20' = 3.333333°
    nav_index_in_sign = int(deg_in_sign / (10.0 / 3.0))
    # Move according to element triplicity
    if rasi_index in [0, 4, 8]:  # Fire (Aries, Leo, Sag) -> starts Aries (0)
        nav_rasi = (0 + nav_index_in_sign) % 12
    elif rasi_index in [1, 5, 9]:  # Earth (Taurus, Virgo, Cap) -> starts Capricorn (9)
        nav_rasi = (9 + nav_index_in_sign) % 12
    elif rasi_index in [2, 6, 10]:  # Air (Gemini, Libra, Aqu) -> starts Libra (6)
        nav_rasi = (6 + nav_index_in_sign) % 12
    else:  # Water (Cancer, Scorpio, Pisces) -> starts Cancer (3)
        nav_rasi = (3 + nav_index_in_sign) % 12

    return {
        "name": name,
        "sign": rasi_index + 1,
        "sign_name": SIGN_NAMES[rasi_index],
        "degree": round(deg_in_sign, 6),
        "longitude": round(abs_long, 6),
        "nakshatra": NAKSHATRAS[nak_idx],
        "pada": pada,
        "house": house,
        "sign_lord": sign_lord,
        "nakshatra_lord": nak_lord,
        "navamsha_sign": nav_rasi + 1,
        "navamsha_sign_name": SIGN_NAMES[nav_rasi],
    }


@app.get("/")
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Parrot Cards Astro Engine",
        "engine": "pyJHora",
        "calculation_method": "drik (Drik Siddhant)",
        "ayanamsa": "TRUE_PUSHYA (Pushya Paksha Ayanamsa)",
        "version": "1.0.0",
    }


@app.post("/horoscope")
def calculate_horoscope(req: HoroscopeRequest):
    try:
        # Enforce Swiss Ephemeris data path
        if os.path.exists(EPHE_PATH):
            swe.set_ephe_path(EPHE_PATH)

        # Enforce Drik Siddhant and Pushya Paksha Ayanamsa
        drik.set_ayanamsa_mode("TRUE_PUSHYA")
        const.set_astrology_model(1)

        # Parse date and time
        date_parts = [int(p) for p in req.date.strip().split("-")]
        year, month, day = date_parts[0], date_parts[1], date_parts[2]

        time_parts = [int(float(p)) for p in req.time.strip().split(":")]
        hour = time_parts[0]
        minute = time_parts[1]
        second = time_parts[2] if len(time_parts) > 2 else 0

        dob = Date(year, month, day)
        tob = (hour, minute, second)
        place = drik.Place(req.place or "Unknown", req.latitude, req.longitude, req.timezone)

        # Julian Day calculation (Local birth time JD for PyJHora)
        # Note: PyJHora's charts.divisional_chart internally converts jd_at_dob to UTC
        # by subtracting place.timezone / 24. Passing pre-converted jd_utc would cause
        # the timezone offset to be subtracted twice (double shift).
        jd_local = utils.julian_day_number((year, month, day), tob)

        # 1. Primary D-1 Rasi Chart
        d1 = charts.divisional_chart(jd_local, place, divisional_chart_factor=1)
        lag_entry = next((x for x in d1 if x[0] == "L"), None)
        if not lag_entry:
            raise ValueError("Lagna calculation failed in D-1 chart")
        lag_rasi = int(lag_entry[1][0])

        # 2. Primary D-9 Navamsa Chart
        d9 = charts.divisional_chart(jd_local, place, divisional_chart_factor=9)
        d9_lag_entry = next((x for x in d9 if x[0] == "L"), None)
        d9_lag_rasi = int(d9_lag_entry[1][0]) if d9_lag_entry else 0

        # 3. Special Lagnas
        special_lagnas_raw = charts.special_lagna_longitudes(dob, tob, place)

        # 4. Varnada Lagnas (V1 to V12)
        varnadas_raw = charts.varnada_lagna_longitudes(dob, tob, place)

        # 5. Upagrahas
        upagrahas_raw = charts.special_planet_longitudes(dob, tob, place)

        # 6. Sphutas
        sphutas_raw = charts.sphuta_longitudes(dob, tob, place)

        # 7. Arudhas (A1 / Arudha Lagna to A12)
        arudhas_raw = charts.arudha_lagna_longitudes(dob, tob, place)

        # 8. Chara Karakas
        chara_karakas_raw = charts.chara_karakas(d1)

        # 9. Planetary States (Retrograde & Combustion)
        try:
            retrograde_planets = [PLANET_NAMES[p] for p in charts.planets_in_retrograde(d1) if p in PLANET_NAMES]
        except Exception:
            retrograde_planets = []

        try:
            combust_planets = [PLANET_NAMES[p] for p in charts.planets_in_combustion(d1) if p in PLANET_NAMES]
        except Exception:
            combust_planets = []

        # ================= BUILD DATA ARRAYS =================
        nakshatra_pada = []
        d1_list = []
        d9_list = []

        # D1 Lagna
        lag_point = make_point("Lagna", lag_rasi, lag_entry[1][1], lag_rasi)
        nakshatra_pada.append(lag_point)
        d1_list.append(lag_point)

        # D1 Planets
        planets_by_id = {}
        for item in d1:
            p_id = item[0]
            if isinstance(p_id, int) and p_id in PLANET_NAMES:
                p_name = PLANET_NAMES[p_id]
                pt = make_point(p_name, item[1][0], item[1][1], lag_rasi)
                nakshatra_pada.append(pt)
                d1_list.append(pt)
                planets_by_id[p_id] = pt

        # D9 List
        for item in d9:
            p_id = item[0]
            if p_id == "L":
                d9_list.append(make_point("Lagna", item[1][0], item[1][1], d9_lag_rasi))
            elif isinstance(p_id, int) and p_id in PLANET_NAMES:
                d9_list.append(make_point(PLANET_NAMES[p_id], item[1][0], item[1][1], d9_lag_rasi))

        # Special Lagnas
        special_lagnas = []
        for code, pos in special_lagnas_raw:
            name = SPECIAL_LAGNA_NAMES.get(code, code)
            pt = make_point(name, pos[0], pos[1], lag_rasi)
            special_lagnas.append(pt)
            nakshatra_pada.append(pt)

        # Arudha Lagna (from A1)
        a1_entry = next((x for x in arudhas_raw if x[0] == "A1"), None)
        if a1_entry:
            al_pt = make_point("Arudha Lagna", a1_entry[1][0], a1_entry[1][1], lag_rasi)
            special_lagnas.append(al_pt)
            nakshatra_pada.append(al_pt)

        # Paka Lagna (Lord of Janma Lagna position)
        lag_lord_name = SIGN_LORDS[lag_rasi]
        lag_lord_pt = next((p for p in nakshatra_pada if p["name"] == lag_lord_name), None)
        if lag_lord_pt:
            paka_pt = make_point("Paka Lagna", lag_lord_pt["sign"] - 1, lag_lord_pt["degree"], lag_rasi)
            special_lagnas.append(paka_pt)
            nakshatra_pada.append(paka_pt)

        # House Varnadas
        house_varnadas = []
        for code, pos in varnadas_raw:
            pt = make_point(code, pos[0], pos[1], lag_rasi)
            house_varnadas.append(pt)
            nakshatra_pada.append(pt)

        # Upagrahas
        upagrahas = []
        for code, pos in upagrahas_raw:
            name = UPAGRAHA_NAMES.get(code, code)
            pt = make_point(name, pos[0], pos[1], lag_rasi)
            upagrahas.append(pt)
            nakshatra_pada.append(pt)

        # Sphutas
        sphutas = []
        for code, pos in sphutas_raw:
            name = SPHUTA_NAMES.get(code, code)
            pt = make_point(name, pos[0], pos[1], lag_rasi)
            sphutas.append(pt)
            nakshatra_pada.append(pt)

        # Brahma Sphuta: (Lagna_long + Jupiter_long) % 360
        jup_pt = planets_by_id.get(4)  # 4 = Jupiter
        if jup_pt:
            brahma_abs = (lag_point["longitude"] + jup_pt["longitude"]) % 360.0
            brahma_sign = int(brahma_abs / 30.0)
            brahma_deg = brahma_abs % 30.0
            brahma_pt = make_point("Brahma Sphuta", brahma_sign, brahma_deg, lag_rasi)
            sphutas.append(brahma_pt)
            nakshatra_pada.append(brahma_pt)

        # Formatted Chara Karakas
        chara_karakas = {}
        for p_id, k_list in chara_karakas_raw.items():
            if p_id in PLANET_NAMES and k_list:
                p_name = PLANET_NAMES[p_id]
                kar_key = k_list[0]
                chara_karakas[kar_key] = p_name

        response_data = {
            "engine": "pyJHora",
            "calculation_method": "drik",
            "ayanamsa": "TRUE_PUSHYA",
            "ayanamsa_name": "Pushya Paksha Ayanamsa",
            "horoscope": {
                "ayanamsa": "Pushya Paksha (TRUE_PUSHYA)",
                "engine_revision": "pyJHora-drik-pushyapaksha-v1",
                "nakshatra_pada": nakshatra_pada,
                "special_lagnas": special_lagnas,
                "house_varnadas": house_varnadas,
                "upagrahas": upagrahas,
                "sphuta": sphutas,
                "divisional_charts": {
                    "D-1_rasi": d1_list,
                    "D-9_navamsa": d9_list,
                },
                "chara_karakas": chara_karakas,
                "planetary_states": {
                    "retrograde": retrograde_planets,
                    "combust": combust_planets,
                },
            },
        }

        return response_data

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PyJHora calculation error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
