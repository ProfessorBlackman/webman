from typing import List, Dict, Any

from pydantic import BaseModel


class Issue(BaseModel):
    element: str
    issue: str
    src: str | None = None
    text: str | None = None
    type: str | None = None
    id: str | None = None
    role: str | None = None
    missing_attributes: List[str] | None = None

class AccessibilityAnalysisResult(BaseModel):
    url: str
    image_issues: List[Issue]
    heading_issues: List[Issue]
    form_issues: List[Issue]
    contrast_issues: List[Issue]
    aria_issues: List[Issue]
    total_issues: int
    error: str | None = None

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'AccessibilityAnalysisResult':
        return AccessibilityAnalysisResult(**data)
