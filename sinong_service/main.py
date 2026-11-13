from fastapi import FastAPI

from fetch_data import get_weather_data, get_soil_data, get_geographical_data
from models import *
from prompt_builder import build_message
from sinong_ollama import ask_sinong

# run command - uvicorn main:app --port 8001 --reload
app = FastAPI(title="Sinong Service")

def safe_fetch(func, latitude, longitude, warnings, message):
    try:
        return func(latitude, longitude)
    except Exception:
        warnings.append(message)
        return {}

@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    warnings = []
    history = [m.model_dump for m in request.history]

    if history:
        weather = geographical = soil = {}
    else:
        weather = safe_fetch(get_weather_data, request.latitude, request.longitude, warnings, "Weather data unavailable")
        soil = safe_fetch(get_soil_data, request.latitude, request.longitude, warnings, "Soil data unavailable")
        geographical = safe_fetch(get_geographical_data, request.latitude, request.longitude, warnings, "Geographical data unavailable")

    messages = build_message(question=request.question, geographical_dataa=geographical, weather_data=weather,
                             soil_data=soil, farm_info=request.farm.model_dump() if request.farm else None ,
                             soil_override=request.soil_override.model_dump() if request.soil_override else None,
                             history=history, think=request.think)

    answer = ask_sinong(messages)

    return AskResponse(
        answer=answer,
        language=request.language,
        data_used={"weather": bool(weather), "location": bool(geographical), "soil": bool(soil)},
        warnings=warnings,
        model="Sinong 8B",
        prompt=messages[-1]["content"] if request.debug else None
    )