"""Chequeos de consistencia de los datos simulados."""

import json

from viajes.config import DATA_DIR


def load(name):
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def test_flights_reference_known_cities_and_currencies():
    cities = {c["name"] for c in load("cities.json")}
    rates = load("exchange_rates.json")["rates"]
    for f in load("flights.json"):
        assert f["origin"] in cities
        assert f["destination"] in cities
        assert f["currency"] in rates
        assert f["price"] > 0


def test_flight_ids_are_unique():
    ids = [f["id"] for f in load("flights.json")]
    assert len(ids) == len(set(ids))


def test_weather_covers_every_city_and_month():
    cities = {c["name"] for c in load("cities.json")}
    weather = load("weather.json")
    assert set(weather) == cities
    for months in weather.values():
        assert [m["month"] for m in months] == list(range(1, 13))


def test_example_route_exists_mendoza_bariloche_july():
    flights = load("flights.json")
    assert any(
        f["origin"] == "Mendoza" and f["destination"] == "Bariloche" and f["date"].startswith("2027-07")
        for f in flights
    )
