from datetime import date

SYSTEM_PROMPT = """You are an agronomy advisor for farmers in North Macedonia and the Balkans.

Rules:
- Base your advice on the location, farm, weather and soil data provided.
- Give answers based on the season - current and a couple weeks in the future. 
- Values marked "estimate" are approximate; farmer and lab values are more reliable.
- If important information is missing (e.g. the crop), say what is missing and keep the advice general.
- Do not give exact fertilizer or pesticide doses unless soil test data is provided; recommend a soil test instead.
- Be practical and concise. Farmers need clear actions, not theory.

Answer structure:
1. Situation – what the data shows that is relevant to the question
2. Recommended actions – concrete steps
3. What to monitor – signs to watch in the coming days

Only give answers in English."""


def format_location(geographical_data, elevation):
    parts = [geographical_data.get("city"), geographical_data.get("county"), geographical_data.get("country")]
    parts = list(dict.fromkeys(p for p in parts if p))
    today = date.today()

    return "\n".join([
        "## Date and Location",
        f"- Date: {today.day} {today:%B} {today.year}",
        f"- Location: {', '.join(p for p in parts if p)}",
        f"- Elevation: {elevation} m"
    ])

def format_weather(weather_data):
    return "\n".join([
        "## Weather",
        f"- Now: {int(weather_data['temperature_now'])} {weather_data['temperature_unit']}, "
        f"humidity {weather_data['relative_humidity_now']} {weather_data['relative_humidity_unit']}, "
        f"wind {weather_data['wind_speed_now']} {weather_data['wind_speed_unit']}",
        f"- Today: min {weather_data['temperature_min_today']} {weather_data['temperature_unit']} / "
        f"max {weather_data['temperature_max_today']} {weather_data['temperature_unit']}",
        f"- Lowest temperature next 7 days: {weather_data['lowest_temp_next_7d']} {weather_data['temperature_unit']}",
        f"- Rain last 7 days: {weather_data['rain_last_7d']} {weather_data['rain_unit']}",
        f"- Rain next 7 days: {weather_data['rain_next_7d']} {weather_data['rain_unit']}",
        f"- Evapotranspiration last 7 days: {weather_data['et0_last_7d']} {weather_data['et0_unit']}",
    ])

def format_soil(soil_data, weather, override=None):
    soil_data = soil_data or {}
    weather = weather or {}
    override = override or {}

    moisture = weather.get("soil_moisture_3_9cm")
    moisture_pct = moisture * 100 if moisture is not None else None

    soc = soil_data.get("soc")
    organic_matter = soc * 1.72 / 10 if soc is not None else None

    if override.get("ph") is not None:
        ph_line = f"- pH: {override['ph']} (farmer/lab value)"
    else:
        ph_line = f"- pH (in water): {soil_data.get('phh2o')} (estimate)"

    lines = [
        "## Soil",
        "Current conditions (Open-Meteo model):",
        f"- Temperature at 6 cm: {weather.get('soil_temperature_6cm')} °C",
        f"- Moisture at 3–9 cm: {moisture_pct}%",
        "Properties (SoilGrids estimate, 5–15 cm):",
        f"- Clay: {soil_data.get('clay')}%",
        f"- Sand: {soil_data.get('sand')}%",
        f"- Silt: {soil_data.get('silt')}%",
        ph_line,
        f"- Organic matter: {organic_matter}%",
        f"- Cation exchange capacity (CEC): {soil_data.get('cec')}cmol(c)/kg",
        f"- Total nitrogen: {soil_data.get('nitrogen')} g/kg (not plant-available N)",
    ]

    if override.get("soil_type"):
        lines.append(f"- Soil type: {override['soil_type']} (farmer report)")
    if override.get("drainage"):
        lines.append(f"- Drainage: {override['drainage']} (farmer report)")

    return "\n".join(lines)


def format_farm_data(farm_info):
    labels = {
        "crop": 'Crop',
        'growth_stage': "Growth stage",
        'planting_date': "Planting date",
        'setup': "Growing Setup",
        'irrigation': "Irrigation",
        'previous_crop': "Previous crop",
        'recent_treatments': "Recent treatments",
        'symptoms': "Symptoms"
    }

    lines = ["## Farm"]

    for key, val in labels.items():
        if farm_info.get(key) is not None:
            lines.append(f"- {val}: {farm_info.get(key)}")

    if len(lines) == 1:
        lines.append("No farm info provided.")

    return "\n".join(lines)

def build_message(question, geographical_dataa, soil_data, weather_data,
                  farm_info = None, soil_override = None, history = None, think=False):

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if history:
        messages += history
        if think:
            messages.append({"role": "user", "content": question})
        else:
            messages.append({"role": "user", "content": question + " /no_think"})
        return messages

    parts = [
        format_location(geographical_dataa, weather_data.get('elevation')),
        format_farm_data(farm_info or {}),
        format_weather(weather_data),
        format_soil(soil_data, weather_data, soil_override),
        f"## Question: {question}",
    ]

    user_prompt = "\n\n".join(parts)
    if think:
        messages.append({"role": "user", "content": user_prompt})
    else:
        messages.append({"role": "user", "content": user_prompt + " /no_think"})

    return messages
