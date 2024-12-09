from typing import Dict, Any
from pydantic import BaseModel

class ViewportTestResult(BaseModel):
    has_horizontal_scroll: bool
    elements_overflow: bool

class ResourceLoadingResult(BaseModel):
    duration: float
    size: int

class InteractiveElementResult(BaseModel):
    visible: bool
    clickable: bool

class Results(BaseModel):
    viewport_tests: Dict[str, ViewportTestResult]
    resource_loading: Dict[str, ResourceLoadingResult]
    interactive_elements: Dict[str, InteractiveElementResult]
    load_time: float

class WebpageResponsivenessReport(BaseModel):
    url: str
    timestamp: str
    results: Dict[str, Any]

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'WebpageResponsivenessReport':
        return WebpageResponsivenessReport(**data)