from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Location:
    name: str
    latitude: float
    longitude: float
    timezone: str = "Asia/Shanghai"


@dataclass(frozen=True, slots=True)
class Recipient:
    id: str
    name: str
    openid: str
    location: Location
    signoff: str


@dataclass(frozen=True, slots=True)
class WeatherSnapshot:
    weather_code: int
    current_temperature: float
    apparent_temperature: float
    humidity: int
    wind_speed: float
    temperature_min: float
    temperature_max: float
    precipitation_probability: int
    uv_index_max: float


@dataclass(frozen=True, slots=True)
class TemplateMessage:
    fields: dict[str, dict[str, str]]

    def as_payload(self, openid: str, template_id: str) -> dict[str, Any]:
        return {
            "touser": openid,
            "template_id": template_id,
            "data": self.fields,
        }

