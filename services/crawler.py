import asyncio
import requests
from bs4 import BeautifulSoup
from pyppeteer import launch

from dtos.responses.performance_response import PerformanceReport


async def perform_website_crawl(url: str) -> PerformanceReport:
    """
    Perform comprehensive website performance crawl

    Args:
        url (str): Website URL to analyze

    Returns:
        dict: Performance analysis results
    """
    # Measure load time and fetch HTML content
    response = _fetch_html_and_response_time(url)

    # Check mobile-friendliness using Pyppeteer
    browser = await launch()
    page = await browser.newPage()
    await page.setViewport({'width': 375, 'height': 667})  # Mobile device size
    await page.goto(url)

    # Parse content
    soup = BeautifulSoup(response[0].text, 'html.parser')

    # Simulate performance analysis
    performance_report = {
        'url': url,
        'load_time': response[1],
        'mobile_friendly': page.viewport['width'] <= 480,
        'seo_score': _calculate_seo_score(soup),
        'accessibility_score': _calculate_accessibility_score(soup),
        'security_headers': _check_security_headers(response[0].headers)
    }

    print("performance_report")
    print(performance_report)

    await browser.close()
    return PerformanceReport.from_dict(data=performance_report)

def _fetch_html_and_response_time(url: str) -> tuple:
    """
    Fetch HTML content and response time for a given URL

    Args:
        url (str): Website URL

    Returns:
        tuple: Tuple containing HTML content and response time
    """
    start_time = asyncio.get_event_loop().time()
    response = requests.get(url, timeout=10)
    return response, asyncio.get_event_loop().time() - start_time


def _calculate_seo_score(soup: BeautifulSoup) -> float:
    """
    Calculate basic SEO score based on content

    Args:
        soup (BeautifulSoup): Parsed HTML

    Returns:
        float: SEO score (0-100)
    """
    score = 100

    # Check title tag
    if not soup.find('title'):
        score -= 10

    # Check meta description
    if not soup.find('meta', attrs={'name': 'description'}):
        score -= 15

    # Check heading structure
    if not soup.find(['h1', 'h2']):
        score -= 10

    return max(0, score)


def _calculate_accessibility_score(soup: BeautifulSoup) -> float:
    """
    Calculate basic accessibility score

    Args:
        soup (BeautifulSoup): Parsed HTML

    Returns:
        float: Accessibility score (0-100)
    """
    score = 100

    # Check alt text on images
    images_without_alt = soup.find_all('img', alt=False)
    score -= len(images_without_alt) * 5

    # Check color contrast (simplified)
    # In a real implementation, this would be more complex

    return max(0, score)


def _check_security_headers(headers: dict) -> dict:
    """
    Check security-related headers

    Args:
        headers (dict): HTTP response headers

    Returns:
        dict: Security header analysis
    """
    return {
        'x_frame_options': headers.get('X-Frame-Options', 'Missing'),
        'x_xss_protection': headers.get('X-XSS-Protection', 'Missing'),
        'content_security_policy': headers.get('Content-Security-Policy', 'Missing'),
        'strict_transport_security': headers.get('Strict-Transport-Security', 'Missing')
    }
