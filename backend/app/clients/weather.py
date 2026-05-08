"""Weather client — open-meteo backed forecasts (no API key required).

Implementation lands in Phase 4 (only used by stretch auto-detection).
For v1 the demo surface synthesises weather disruptions directly.
"""

from typing import Protocol

from pydantic import BaseModel


class WeatherForecast(BaseModel):
    day_iso: str
    period: str
    condition: str
    precipitation_mm: float
    temperature_c: float


class WeatherClient(Protocol):
    async def forecast(
        self, lat: float, lng: float, days: int = 7
    ) -> list[WeatherForecast]: ...


class OpenMeteoClient:
    """Free, no-key weather data for demo + stretch auto-detection."""

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self._timeout = timeout_seconds

    async def forecast(
        self, lat: float, lng: float, days: int = 7
    ) -> list[WeatherForecast]:
        raise NotImplementedError("OpenMeteoClient.forecast — only needed for stretch")
