from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from dtos.requests.website_analysis import WebsiteAnalysisRequest
from dtos.responses.accessibility_response import AccessibilityAnalysisResult
from dtos.responses.performance_response import WebVitalsResult
from dtos.responses.responsiveness_response import WebpageResponsivenessReport
from log_management.logging_config import setup_logging, main_logger
from services.performance_analyzer import WebPageAnalyzer
from services.responsiveness_analyzer import WebpageResponsivenessAnalyzer
from services.validators import validate_url
from services.web_accessibility_analyzer import WebAccessibilityAnalyzer

app = FastAPI(
    title="webman",
    description="Analyze website performance and generate comprehensive reports"
)

# Define allowed origins
origins = [
    "http://localhost:5173",
    "http://localhost:8080",
    "https://webman-frontend.vercel.app",
    "https://web-wizard-insights.vercel.app"
    # Add more origins as needed
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows all origins if set to ["*"]
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# setup logging
setup_logging(app)

# init celery
from celery_config import make_celery

celery = make_celery(app)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/analyze_performance", response_model=WebVitalsResult)
async def analyze_website(request: WebsiteAnalysisRequest):
    """
    Endpoint to trigger website performance analysis

    Args:
        request (WebsiteAnalysisRequest): Contains the website URL to analyze

    Returns:
        PerformanceReport: Comprehensive performance analysis results
    """
    print(f"Analyzing website: {request.url}")
    # Validate URL
    try:
        validated_url = validate_url(request.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Perform crawl and analysis
    try:
        performance_analyzer = WebPageAnalyzer()

        performance_report = performance_analyzer.analyze(validated_url)

        return performance_report
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/analyze_responsiveness", response_model=WebpageResponsivenessReport)
async def analyze_responsiveness(request: WebsiteAnalysisRequest):
    """
    Endpoint to trigger mobile friendliness analysis

    Args:
        request (WebsiteAnalysisRequest): Contains the website URL to analyze

    Returns:
        dict: Mobile friendliness analysis results
    """
    print(f"Analyzing mobile friendliness: {request.url}")
    # Validate URL
    try:
        validated_url = validate_url(request.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Perform mobile friendliness analysis
    try:
        # Initialize mobile friendliness analyzer
        mobile_analyzer = WebpageResponsivenessAnalyzer(url=validated_url)
        mobile_friendly_results = mobile_analyzer.run_full_analysis()
        print("mobile_friendly_results")
        print(mobile_friendly_results)

        return mobile_friendly_results
    except Exception as e:
        main_logger.error(e)
        raise HTTPException(status_code=500, detail=f"Mobile friendliness analysis failed: {str(e)}")


@app.post("/analyze_accessibility", response_model=AccessibilityAnalysisResult)
async def analyze_accessibility(request: WebsiteAnalysisRequest):
    """
    Endpoint to trigger website accessibility analysis

    Args:
        request (WebsiteAnalysisRequest): Contains the website URL to analyze

    Returns:
        AccessibilityAnalysisResult: Comprehensive accessibility analysis results
    """
    print(f"Analyzing accessibility: {request.url}")
    # Validate URL
    try:
        validated_url = validate_url(request.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Perform accessibility analysis
    try:
        # Initialize mobile friendliness analyzer
        accessibility_analyzer = WebAccessibilityAnalyzer(url=validated_url)
        accessibility_results = accessibility_analyzer.analyze()

        print("accessibility_results")
        print(accessibility_results)

        return accessibility_results
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Accessibility analysis failed: {str(e)}")
