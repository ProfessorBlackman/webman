from pydantic import BaseModel


class WebsiteAnalysisRequest(BaseModel):
    url: str
    analysis_type: str