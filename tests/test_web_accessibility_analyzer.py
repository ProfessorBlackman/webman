import pytest
from unittest.mock import Mock, patch
import requests
from bs4 import BeautifulSoup

from services.web_accessibility_analyzer import WebAccessibilityAnalyzer


@pytest.fixture
def mock_requests_get():
    """Mock requests.get to simulate web page responses"""
    with patch('requests.get') as mock_get:
        yield mock_get


@pytest.fixture
def analyzer():
    """Create a WebAccessibilityAnalyzer instance"""
    return WebAccessibilityAnalyzer("https://example.com")


def test_load_page_success(analyzer, mock_requests_get):
    """Test successful page loading"""
    # Create a mock response
    mock_response = Mock()
    mock_response.text = "<html><body>Test Page</body></html>"
    mock_response.raise_for_status = Mock()
    mock_requests_get.return_value = mock_response

    # Call load_page
    result = analyzer.load_page()

    # Assertions
    assert result is True
    assert analyzer.soup is not None
    assert isinstance(analyzer.soup, BeautifulSoup)
    mock_requests_get.assert_called_once_with("https://example.com")


def test_load_page_failure(analyzer, mock_requests_get):
    """Test page loading failure"""
    # Simulate a request exception
    mock_requests_get.side_effect = requests.RequestException("Connection error")

    # Call load_page
    result = analyzer.load_page()

    # Assertions
    assert result is False
    assert analyzer.soup is None
    assert len(analyzer.issues) == 1
    assert "Error loading page" in analyzer.issues[0]


def test_check_images_alt(analyzer):
    """Test checking images for missing alt text"""
    # Create a mock BeautifulSoup object with test images
    html_content = """
    <html>
        <body>
            <img src="image1.jpg">
            <img src="image2.jpg" alt="">
            <img src="image3.jpg" alt="Description">
        </body>
    </html>
    """
    analyzer.soup = BeautifulSoup(html_content, 'html.parser')

    # Call the method
    issues = analyzer.check_images_alt()

    # Assertions
    assert len(issues) == 2
    assert issues[0]['element'] == 'img'
    assert issues[0]['src'] == 'image1.jpg'
    assert issues[0]['issue'] == 'Missing alt text'


def test_check_heading_hierarchy(analyzer):
    """Test checking heading hierarchy"""
    # Create a mock BeautifulSoup object with test headings
    html_content = """
    <html>
        <body>
            <h1>Main Heading</h1>
            <h3>Skipped Heading</h3>
            <h2>Correct Hierarchy</h2>
        </body>
    </html>
    """
    analyzer.soup = BeautifulSoup(html_content, 'html.parser')

    # Call the method
    issues = analyzer.check_heading_hierarchy()

    # Assertions
    assert len(issues) == 1
    assert issues[0]['element'] == 'h3'
    assert 'Skipped heading level' in issues[0]['issue']


def test_check_form_labels(analyzer):
    """Test checking form inputs for associated labels"""
    # Create a mock BeautifulSoup object with test form inputs
    html_content = """
    <html>
        <body>
            <input type="text" id="username">
            <label for="email">Email</label>
            <input type="email" id="email">
        </body>
    </html>
    """
    analyzer.soup = BeautifulSoup(html_content, 'html.parser')

    # Call the method
    issues = analyzer.check_form_labels()

    # Assertions
    assert len(issues) == 1
    assert issues[0]['element'] == 'input'
    assert issues[0]['id'] == 'username'
    assert issues[0]['issue'] == 'Missing associated label'


def test_check_color_contrast(analyzer):
    """Test checking color contrast"""
    # Create a mock BeautifulSoup object with test elements
    html_content = """
    <html>
        <body>
            <p style="color: #000;">Dark text</p>
            <div style="color: red;">Colored div</div>
            <span>No color</span>
        </body>
    </html>
    """
    analyzer.soup = BeautifulSoup(html_content, 'html.parser')

    # Call the method
    issues = analyzer.check_color_contrast()

    # Assertions
    assert len(issues) == 2
    assert all('potential color contrast issue' in issue['issue'].lower() for issue in issues)


def test_check_aria_attributes(analyzer):
    """Test checking ARIA attributes"""
    # Create a mock BeautifulSoup object with test ARIA elements
    html_content = """
    <html>
        <body>
            <div role="checkbox"></div>
            <input role="slider">
            <div aria-label=""></div>
            <div aria-describedby="nonexistent-id">Content</div>
        </body>
    </html>
    """
    analyzer.soup = BeautifulSoup(html_content, 'html.parser')

    # Call the method
    issues = analyzer.check_aria_attributes()

    # Assertions
    assert len(issues) >= 3  # Should have multiple ARIA issues


def test_analyze_success(analyzer, mock_requests_get):
    """Test full accessibility analysis success"""
    # Mock requests and BeautifulSoup
    mock_response = Mock()
    mock_response.text = """
    <html>
        <body>
            <img src="test.jpg">
            <h1>Title</h1>
            <input type="text" id="username">
        </body>
    </html>
    """
    mock_response.raise_for_status = Mock()
    mock_requests_get.return_value = mock_response

    # Call analyze method
    result = analyzer.analyze()
    result_dict = dict(result)

    # Assertions
    assert result is not None
    assert 'url' in result_dict
    assert 'total_issues' in result_dict
    assert result_dict['total_issues'] > 0


def test_analyze_load_failure(analyzer, mock_requests_get):
    """Test accessibility analysis with page load failure"""
    # Simulate a request exception
    mock_requests_get.side_effect = requests.RequestException("Connection error")

    # Call analyze method
    result = analyzer.analyze()

    # Assertions
    assert 'error' in result
    assert result['error'] == 'Failed to load page'
