from fastapi import FastAPI, HTTPException

from dtos.requests.website_analysis import WebsiteAnalysisRequest
from dtos.responses.performance_response import PerformanceReport
from log_management.logging_config import setup_logging

app = FastAPI(
    title="webman",
    description="Analyze website performance and generate comprehensive reports"
)

# setup logging
setup_logging(app)

# init celery
from celery_config import make_celery
celery = make_celery(app)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/analyze", response_model=PerformanceReport)
async def analyze_website(request: WebsiteAnalysisRequest):
    """
    Endpoint to trigger website performance analysis

    Args:
        request (WebsiteAnalysisRequest): Contains the website URL to analyze

    Returns:
        PerformanceReport: Comprehensive performance analysis results
    """
    # Validate URL
    try:
        validated_url = validate_url(request.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Perform crawl and analysis
    try:
        performance_report = perform_website_crawl(validated_url)
        return performance_report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

