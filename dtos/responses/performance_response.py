from typing import Dict
from pydantic import BaseModel

class MetricResult(BaseModel):
    value: float
    rating: str
    unit: str

class WebVitalsResult(BaseModel):
    TTFB: MetricResult
    FCP: MetricResult
    LCP: MetricResult
    CLS: MetricResult
    FID: MetricResult

    @staticmethod
    def from_dict(data: Dict[str, Dict[str, float | str]]) -> 'WebVitalsResult':
        return WebVitalsResult(**data)