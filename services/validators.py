import re
from datetime import datetime
from urllib.parse import urlparse


def validate_url(url: str) -> str:
    """
    Validate and normalize input URL

    Args:
        url (str): Input URL to validate

    Returns:
        str: Normalized, valid URL

    Raises:
        ValueError: If URL is invalid
    """
    # Basic URL validation
    if not url:
        raise ValueError("URL cannot be empty")

    # Add http:// if no scheme provided
    if not re.match(r'^https?://', url):
        url = f'http://{url}'

    # Parse and validate URL
    try:
        parsed_url = urlparse(url)
        if not parsed_url.netloc:
            raise ValueError("Invalid URL")

        # Reconstruct normalized URL
        return f"{parsed_url.scheme}://{parsed_url.netloc}"

    except Exception:
        raise ValueError("Invalid URL format")

def validate_timestamp(timestamp: str, format: str = "%Y-%m-%d %H:%M:%S") -> bool:
    try:
        datetime.strptime(timestamp, format)
        return True
    except ValueError:
        return False