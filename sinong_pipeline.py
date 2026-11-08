import datetime
import os
import requests
import json
from dotenv import load_dotenv
import rasterio
from rasterio.warp import transform
from requests.structures import CaseInsensitiveDict

load_dotenv(".env")

def get_weather_data(latitude, longitude):
    res = requests.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
        "hourly": "soil_temperature_6cm,soil_moisture_3_to_9cm",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,et0_fao_evapotranspiration",
        "past_days": 7,
        "forecast_days": 7,
        "timezone": "Europe/Skopje"
    }, timeout=10)

    res.raise_for_status()
    data = res.json()

    daily, hourly, current = data["daily"], data["hourly"], data["current"]
    daily_units, hourly_units, current_units = data["daily_units"], data["hourly_units"], data["current_units"]
    # 7 days before and 7 days in the future - today will be index 7
    today = 7
    # The time format in the current section of the resulting json look like this 2026-11-07T22:00
    hour = current["time"]
    hour_index = hourly["time"].index(hour[:-2] + "00")

    def total(values):
        return round(sum(v for v in values if v is not None), 1)

    return {
        "temperature_now": current["temperature_2m"],
        "temperature_unit": current_units["temperature_2m"],
        "relative_humidity_now": current["relative_humidity_2m"],
        "relative_humidity_unit": current_units["relative_humidity_2m"],
        "wind_speed_now": current["wind_speed_10m"],
        "wind_speed_unit": current_units["wind_speed_10m"],
        "temperature_min_today": daily["temperature_2m_min"][today],
        "temperature_max_today": daily["temperature_2m_max"][today],
        "lowest_temp_next_7d": min(daily["temperature_2m_min"][today+1:]),
        "rain_last_7d": total(daily["precipitation_sum"][:today]),
        "rain_next_7d": total(daily["precipitation_sum"][today+1:]),
        "rain_unit": daily_units["precipitation_sum"],
        "evaporation_today": daily["et0_fao_evapotranspiration"][today],
        "evaporation_unit": daily_units["et0_fao_evapotranspiration"],
        "soil_temperature_6cm": hourly["soil_temperature_6cm"][hour_index],
        "soil_temperature_unit": hourly_units["soil_temperature_6cm"],
        "soil_moisture_3_9cm": hourly["soil_moisture_3_to_9cm"][hour_index],
        "soil_moisture_unit": hourly_units["soil_moisture_3_to_9cm"],
        "elevation": data["elevation"]
    }


def get_geographical_data(latitude, longitude):
    url = "https://api.geoapify.com/v1/geocode/reverse"

    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"

    response = requests.get(url, headers=headers, params={
        "lat": latitude,
        "lon": longitude,
        "apiKey": os.getenv("GEO_API_KEY")
    })

    response.raise_for_status()
    data = response.json()


    return {
        "country": data["features"][0]["properties"]["country"],
        "state": data["features"][0]["properties"]["state"],
        "city": data["features"][0]["properties"]["city"]
    }


def get_soil_data(latitude, longitude):
    url_base = "https://files.isric.org/soilgrids/latest/data"
    props = {
    "clay": 10, "sand": 10, "silt": 10,
    "phh2o": 10, "soc": 10, "cec": 10, "nitrogen": 100,
    }

    cache_key = f"{latitude},{longitude}"

    try:
        with open("soil_data_cache.json", "r") as cache_file:
            _cache = json.load(cache_file)
    except (FileNotFoundError, json.JSONDecodeError):
        _cache = {}

    if cache_key in _cache:
        return _cache.get(f"{latitude},{longitude}")["soil"]

    soil = {}
    for prop, factor in props.items():
        url = f"/vsicurl/{url_base}/{prop}/{prop}_5-15cm_mean.vrt"
        with rasterio.open(url) as src:
            xs, ys = transform("EPSG:4326", src.crs, [longitude], [latitude])
            value = next(src.sample([(xs[0], ys[0])]))[0]
            soil[prop] = None if value == src.nodata else round(float(value) / factor, 1)

    _cache[cache_key] = {
        "date_created": datetime.datetime.now().isoformat(timespec="seconds"),
        "soil": soil
    }
    with open("soil_data_cache.json", "w", encoding="utf-8") as cache_file:
        json.dump(_cache, cache_file, indent=4)

    return soil



