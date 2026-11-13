from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, Field

class FarmInfo(BaseModel):
    crop: Optional[str] = None
    growth_stage: Optional[str] = None
    planting_date: Optional[date] = None
    setup: Optional[str] = None
    irrigation: Optional[str] = None
    previous_crop: Optional[str] = None
    recent_treatments: Optional[str] = None
    symptoms: Optional[str] = None


class SoilOverride(BaseModel):
    ph: Optional[float] = Field(None, ge=3, le=10)
    soil_type: Optional[str] = None
    drainage: Optional[Literal["poor", "moderate", "good"]] = None


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AskRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    question: str = Field(..., min_length=3, max_length=2000)
    language: Literal["mk", "en"] = "mk"
    farm: Optional[FarmInfo] = None
    soil_override: Optional[SoilOverride] = None
    history: list[Message] = Field(default_factory=list, max_length=10)
    think: bool = False
    debug: bool = False


class AskResponse(BaseModel):
    answer: str
    language: str
    data_used: dict[str, object]
    warnings: list[str] = []
    model: str
    prompt: Optional[str] = None