import requests
import json

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
        "temperature_now": f"{current["temperature_2m"]}{current_units["temperature_2m"]}",
        "relative_humidity_now": f"{current["relative_humidity_2m"]}{current_units["relative_humidity_2m"]}",
        "wind_speed_now": f"{current["wind_speed_10m"]}{current_units["wind_speed_10m"]}",
        "temperature_min": f"{daily["temperature_2m_min"][today]}{daily_units["temperature_2m_min"]}",
        "temperature_max": f"{daily["temperature_2m_max"][today]}{daily_units["temperature_2m_max"]}",
        "rain_last_7d": f"{total(daily["precipitation_sum"][:today])}{daily_units["precipitation_sum"]}",
        "rain_next_7d": f"{total(daily["precipitation_sum"][today+1:])}{daily_units["precipitation_sum"]}",
        "et0_fao_evapotranspiration": f"{daily["et0_fao_evapotranspiration"][today]}{daily_units["et0_fao_evapotranspiration"]}",
        "soil_temperature": f"{hourly["soil_temperature_6cm"][hour_index]}{hourly_units["soil_temperature_6cm"]}",
        "soil_moisture": f"{hourly["soil_moisture_3_to_9cm"][hour_index]}{hourly_units["soil_moisture_3_to_9cm"]}",
    }
