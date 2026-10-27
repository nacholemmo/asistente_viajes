"""Genera los datos simulados en data/. Determinístico (semilla fija).

Uso: uv run python scripts/generate_data.py
"""

import json
import random
from datetime import date
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SEED = 42

# --- Ciudades -----------------------------------------------------------------

CITIES = [
    {"name": "Buenos Aires", "iata": "AEP", "country": "Argentina", "currency": "ARS"},
    {"name": "Mendoza", "iata": "MDZ", "country": "Argentina", "currency": "ARS"},
    {"name": "Córdoba", "iata": "COR", "country": "Argentina", "currency": "ARS"},
    {"name": "Rosario", "iata": "ROS", "country": "Argentina", "currency": "ARS"},
    {"name": "Salta", "iata": "SLA", "country": "Argentina", "currency": "ARS"},
    {"name": "Bariloche", "iata": "BRC", "country": "Argentina", "currency": "ARS"},
    {"name": "Ushuaia", "iata": "USH", "country": "Argentina", "currency": "ARS"},
    {"name": "El Calafate", "iata": "FTE", "country": "Argentina", "currency": "ARS"},
    {"name": "Puerto Iguazú", "iata": "IGR", "country": "Argentina", "currency": "ARS"},
    {"name": "Santiago de Chile", "iata": "SCL", "country": "Chile", "currency": "CLP"},
    {"name": "Río de Janeiro", "iata": "GIG", "country": "Brasil", "currency": "BRL"},
    {"name": "Florianópolis", "iata": "FLN", "country": "Brasil", "currency": "BRL"},
    {"name": "Lima", "iata": "LIM", "country": "Perú", "currency": "PEN"},
    {"name": "Cusco", "iata": "CUZ", "country": "Perú", "currency": "PEN"},
]

# --- Tipos de cambio (unidades de moneda por 1 USD) ----------------------------

EXCHANGE_RATES = {
    "base": "USD",
    "as_of": "2026-10-27",
    "note": "Valores simulados, no usar para decisiones reales.",
    "rates": {
        "USD": 1.0,
        "ARS": 1450.0,
        "CLP": 950.0,
        "BRL": 5.4,
        "PEN": 3.7,
        "EUR": 0.92,
        "UYU": 40.5,
    },
}

# --- Rutas --------------------------------------------------------------------
# (origen, destino, precio base en USD, duración en minutos, aerolíneas, meses)
# Cada ruta se genera en ambos sentidos. meses=None => todo el año.
# Los vuelos de cabotaje se cotizan en ARS; los internacionales en USD.

ROUTES = [
    ("Buenos Aires", "Bariloche", 140, 140, ["Aerolíneas Argentinas", "Flybondi", "JetSMART"], None),
    ("Buenos Aires", "Mendoza", 110, 115, ["Aerolíneas Argentinas", "Flybondi", "JetSMART"], None),
    ("Buenos Aires", "Córdoba", 85, 80, ["Aerolíneas Argentinas", "Flybondi", "JetSMART"], None),
    ("Buenos Aires", "Salta", 125, 130, ["Aerolíneas Argentinas", "Flybondi"], None),
    ("Buenos Aires", "Ushuaia", 190, 210, ["Aerolíneas Argentinas", "Flybondi"], None),
    ("Buenos Aires", "El Calafate", 175, 190, ["Aerolíneas Argentinas", "JetSMART"], None),
    ("Buenos Aires", "Puerto Iguazú", 115, 110, ["Aerolíneas Argentinas", "Flybondi", "JetSMART"], None),
    ("Córdoba", "Bariloche", 130, 125, ["Aerolíneas Argentinas", "JetSMART"], None),
    ("Córdoba", "Salta", 95, 90, ["Aerolíneas Argentinas"], None),
    ("Mendoza", "Córdoba", 80, 70, ["Aerolíneas Argentinas"], None),
    # Ruta de temporada de invierno: sólo junio a septiembre.
    ("Mendoza", "Bariloche", 120, 105, ["Aerolíneas Argentinas", "JetSMART"], [6, 7, 8, 9]),
    ("Rosario", "Bariloche", 135, 135, ["Aerolíneas Argentinas"], [1, 2, 6, 7, 8, 12]),
    ("Ushuaia", "El Calafate", 95, 75, ["Aerolíneas Argentinas"], [10, 11, 12, 1, 2, 3]),
    ("Buenos Aires", "Santiago de Chile", 210, 130, ["LATAM", "Aerolíneas Argentinas", "JetSMART"], None),
    ("Mendoza", "Santiago de Chile", 150, 55, ["LATAM", "JetSMART"], None),
    ("Buenos Aires", "Río de Janeiro", 290, 175, ["GOL", "LATAM", "Aerolíneas Argentinas"], None),
    # Florianópolis: sólo temporada de verano.
    ("Buenos Aires", "Florianópolis", 240, 145, ["GOL", "Aerolíneas Argentinas"], [12, 1, 2, 3]),
    ("Buenos Aires", "Lima", 380, 270, ["LATAM"], None),
    ("Lima", "Cusco", 110, 80, ["LATAM", "JetSMART"], None),
]

CHEAP_AIRLINES = {"Flybondi", "JetSMART"}

# Meses en los que hay vuelos: noviembre 2026 a octubre 2027.
MONTHS = [(2026, m) for m in (11, 12)] + [(2027, m) for m in range(1, 11)]
FLIGHTS_PER_ROUTE_MONTH = 3

DEPARTURE_TIMES = ["06:10", "07:45", "09:30", "11:15", "13:40", "16:05", "18:20", "20:50", "22:35"]


def season_multiplier(destination: str, month: int) -> float:
    m = 1.0
    if month == 7:  # vacaciones de invierno
        m *= 1.25
    if month in (1, 2):  # vacaciones de verano
        m *= 1.2
    if destination == "Bariloche" and month in (7, 8):
        m *= 1.35
    if destination in ("Río de Janeiro", "Florianópolis") and month in (1, 2):
        m *= 1.3
    if destination in ("Ushuaia", "El Calafate") and month in (12, 1, 2):
        m *= 1.2
    return m


def is_domestic(origin: str, destination: str) -> bool:
    country = {c["name"]: c["country"] for c in CITIES}
    return country[origin] == "Argentina" and country[destination] == "Argentina"


def generate_flights(rng: random.Random) -> list[dict]:
    flights = []
    ars_per_usd = EXCHANGE_RATES["rates"]["ARS"]

    for a, b, base_usd, duration, airlines, months in ROUTES:
        for origin, destination in ((a, b), (b, a)):
            for year, month in MONTHS:
                if months is not None and month not in months:
                    continue
                days = sorted(rng.sample(range(1, 29), FLIGHTS_PER_ROUTE_MONTH))
                for day in days:
                    airline = rng.choice(airlines)
                    d = date(year, month, day)
                    price_usd = base_usd * season_multiplier(destination, month)
                    price_usd *= rng.uniform(0.85, 1.15)
                    if airline in CHEAP_AIRLINES:
                        price_usd *= 0.8
                    if d.weekday() >= 4:  # viernes a domingo
                        price_usd *= 1.1

                    if is_domestic(origin, destination):
                        price, currency = round(price_usd * ars_per_usd, -2), "ARS"
                    else:
                        price, currency = round(price_usd, 2), "USD"

                    flights.append(
                        {
                            "origin": origin,
                            "destination": destination,
                            "date": d.isoformat(),
                            "departure_time": rng.choice(DEPARTURE_TIMES),
                            "duration_min": duration + rng.choice([-10, -5, 0, 5, 10]),
                            "airline": airline,
                            "stops": 0 if rng.random() < 0.8 else 1,
                            "price": price,
                            "currency": currency,
                            "seats_available": rng.choice([0, 1, 2, 4, 7, 12, 25]),
                        }
                    )

    flights.sort(key=lambda f: (f["date"], f["origin"], f["destination"], f["departure_time"]))
    return [{"id": f"FL{i:04d}", **f} for i, f in enumerate(flights, start=1)]


# --- Clima (promedios mensuales, ene..dic) -------------------------------------
# max °C, min °C, precipitación mm, meses con nieve probable

CLIMATE = {
    "Buenos Aires": ([30, 29, 26, 23, 19, 16, 15, 17, 19, 22, 26, 28], [20, 19, 17, 14, 10, 8, 7, 8, 10, 13, 16, 18], [120, 115, 135, 105, 90, 60, 60, 65, 80, 125, 110, 105], []),
    "Mendoza": ([32, 30, 27, 23, 18, 15, 14, 17, 20, 25, 28, 31], [18, 17, 14, 10, 5, 2, 1, 3, 7, 11, 14, 17], [40, 35, 30, 15, 10, 8, 8, 8, 12, 18, 20, 30], []),
    "Córdoba": ([31, 29, 27, 24, 21, 18, 18, 21, 23, 26, 28, 30], [18, 17, 16, 12, 8, 5, 4, 6, 8, 12, 15, 17], [120, 100, 95, 45, 20, 10, 10, 10, 30, 70, 100, 130], []),
    "Rosario": ([30, 29, 26, 23, 19, 16, 15, 17, 20, 23, 26, 29], [18, 18, 16, 12, 8, 5, 4, 6, 8, 11, 14, 17], [110, 120, 140, 100, 50, 35, 30, 40, 50, 110, 120, 125], []),
    "Salta": ([27, 26, 25, 23, 21, 20, 20, 23, 25, 27, 28, 28], [16, 16, 15, 12, 8, 4, 3, 5, 8, 12, 14, 16], [190, 160, 110, 30, 8, 3, 3, 4, 6, 25, 60, 130], []),
    "Bariloche": ([21, 21, 18, 14, 9, 6, 6, 8, 10, 14, 17, 20], [6, 6, 4, 2, 0, -2, -2, -2, 0, 2, 4, 6], [25, 25, 40, 70, 140, 170, 160, 130, 70, 50, 35, 30], [6, 7, 8, 9]),
    "Ushuaia": ([14, 14, 12, 9, 6, 4, 4, 5, 7, 10, 12, 13], [5, 5, 3, 1, -1, -3, -3, -2, -1, 1, 3, 4], [50, 45, 55, 55, 50, 45, 40, 40, 35, 35, 40, 50], [5, 6, 7, 8, 9, 10]),
    "El Calafate": ([19, 19, 16, 12, 7, 4, 3, 5, 9, 13, 16, 18], [6, 6, 4, 1, -2, -4, -5, -3, -1, 2, 4, 5], [10, 10, 10, 15, 20, 20, 20, 15, 10, 10, 10, 10], [6, 7, 8]),
    "Puerto Iguazú": ([33, 32, 31, 28, 25, 23, 23, 25, 27, 29, 31, 32], [21, 21, 20, 17, 14, 12, 11, 13, 15, 17, 19, 20], [170, 150, 140, 160, 170, 130, 100, 90, 140, 200, 170, 170], []),
    "Santiago de Chile": ([30, 29, 27, 23, 18, 15, 15, 17, 19, 23, 26, 29], [13, 13, 11, 8, 6, 4, 3, 4, 6, 8, 10, 12], [1, 1, 4, 13, 55, 80, 75, 55, 25, 13, 6, 2], []),
    "Río de Janeiro": ([30, 31, 30, 28, 27, 26, 25, 26, 26, 27, 28, 29], [24, 24, 23, 22, 20, 19, 18, 19, 19, 20, 21, 23], [140, 120, 130, 110, 80, 55, 45, 45, 55, 90, 105, 140], []),
    "Florianópolis": ([29, 29, 28, 26, 23, 21, 20, 21, 22, 24, 26, 28], [21, 22, 21, 18, 15, 13, 12, 13, 15, 17, 19, 20], [190, 200, 160, 110, 100, 80, 90, 95, 130, 140, 140, 160], []),
    "Lima": ([26, 27, 26, 24, 22, 20, 19, 19, 20, 21, 23, 25], [19, 20, 19, 18, 16, 15, 15, 15, 15, 16, 17, 18], [1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0], []),
    "Cusco": ([19, 19, 19, 20, 20, 19, 19, 20, 21, 21, 21, 20], [7, 7, 6, 4, 1, -1, -2, 0, 3, 5, 6, 7], [160, 140, 110, 40, 10, 5, 5, 10, 25, 50, 80, 120], []),
}


def describe(temp_max: int, precip: int, snow: bool) -> str:
    if temp_max >= 27:
        temp = "caluroso"
    elif temp_max >= 20:
        temp = "templado"
    elif temp_max >= 12:
        temp = "fresco"
    else:
        temp = "frío"

    if snow:
        rain = "con nevadas frecuentes"
    elif precip >= 150:
        rain = "muy lluvioso"
    elif precip >= 60:
        rain = "con lluvias ocasionales"
    else:
        rain = "mayormente seco"
    return f"{temp}, {rain}"


def generate_weather() -> dict:
    weather = {}
    for city, (maxs, mins, precs, snow_months) in CLIMATE.items():
        weather[city] = []
        for month in range(1, 13):
            snow = month in snow_months
            weather[city].append(
                {
                    "month": month,
                    "avg_max_c": maxs[month - 1],
                    "avg_min_c": mins[month - 1],
                    "precipitation_mm": precs[month - 1],
                    "snow": snow,
                    "summary": describe(maxs[month - 1], precs[month - 1], snow),
                }
            )
    return weather


def write_json(name: str, payload) -> None:
    path = DATA_DIR / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"escrito {path.relative_to(DATA_DIR.parent)}")


def main() -> None:
    rng = random.Random(SEED)
    DATA_DIR.mkdir(exist_ok=True)
    write_json("cities.json", CITIES)
    write_json("exchange_rates.json", EXCHANGE_RATES)
    write_json("weather.json", generate_weather())
    flights = generate_flights(rng)
    write_json("flights.json", flights)
    print(f"{len(flights)} vuelos")


if __name__ == "__main__":
    main()
