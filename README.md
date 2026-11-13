# Parrot Cards Cosmic Astrology Engine

High-precision Vedic astrological calculation microservice built with **FastAPI** and **PyJHora**, backed by the **Swiss Ephemeris**.

## Core Features

- **Calculation Method:** Drik Siddhanta (`ASTROLOGY_MODELS.DRIK = 1`)
- **Ayanamsa:** Pushya Paksha Ayanamsa (`TRUE_PUSHYA`)
- **Divisional Charts:** D-1 (Rasi), D-9 (Navamsha)
- **Comprehensive Vedic Placements:**
  - 9 Planets (Sun to Ketu) + Lagna (Ascendant)
  - 9 Special Lagnas (`BL`, `HL`, `GL`, `PL`, `VL`, `KL`, `BBL`, `SL`, `IL`)
  - Paka Lagna & Arudha Lagna (A1)
  - 12 Varnadas (`V1` to `V12`)
  - 11 Upagrahas (`Kaala`, `Mrityu`, `Ardhaprahara`, `Yamaghantaka`, `Gulika`, `Maandi`, `Dhuma`, `Vyatipata`, `Parivesha`, `Indra Chapa`, `Upaketu`)
  - 15 Sphutas (`Tri`, `Chatur`, `Pancha`, `Prana`, `Deha`, `Mrityu`, `Sookshma Tri`, `Beeja`, `Kshetra`, `Tithi`, `Yoga`, `Rahu Tithi`, `Yogi`, `Avayogi`, `Brahma Sphuta`)
  - 8 Chara Karakas (Atma Karaka to Dara Karaka)
  - Planetary States (Retrogrades, Combustions, Direct)

---

## Prerequisites

- Python 3.10 or 3.11
- C++ Build Tools (required by `pyswisseph` on Windows, or `build-essential` on Linux)

---

## Quickstart (Local)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Server
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
The service will be live at `http://127.0.0.1:8000`.
- **Interactive API Docs (Swagger):** `http://127.0.0.1:8000/docs`
- **Health Check:** `http://127.0.0.1:8000/health`

---

## API Endpoints

### `GET /health`
Returns service status, ephemeris data presence, and configured calculation model.

### `POST /horoscope`
Calculates comprehensive astronomical placements for a birth chart.

**Request Body:**
```json
{
  "year": 1995,
  "month": 10,
  "day": 24,
  "hour": 6,
  "minute": 30,
  "second": 0,
  "latitude": 28.6139,
  "longitude": 77.2090,
  "timezone": 5.5,
  "altitude": 0
}
```

---

## Run Tests

A complete mathematical and astronomical audit test suite is included:

```bash
python tests/test_audit.py
```

Tests verify:
1. Swiss Ephemeris data files presence
2. Drik Siddhanta explicit enforcement
3. True Pushya vs. Lahiri offset delta validation
4. Single timezone Julian Day conversion accuracy (Sunrise / Lagna alignment)
5. 100% parity between direct PyJHora calls and FastAPI endpoint wrapper
6. Mathematical validation of Nakshatra & Navamsha calculations
7. Diurnal solar progression across Sunrise (H1), Midheaven (H10), and Sunset (H7)

---

## Docker Deployment

Build and run using Docker:

```bash
# Build Docker image
docker build -t parrot-astro-engine .

# Run container
docker run -d -p 8000:8000 --name parrot-astro-engine parrot-astro-engine
```

Compatible with:
- **Render** (Web Service, Docker or Python runtime)
- **Railway** (Docker)
- **Fly.io**
- **AWS ECS / DigitalOcean App Platform**

---

## License

Proprietary calculation engine for Parrot Cards. PyJHora components licensed under their respective open-source licenses.

