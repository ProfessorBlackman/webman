import pytest
from unittest.mock import Mock, patch

from services.responsiveness_analyzer import WebpageResponsivenessAnalyzer
from services.validators import validate_timestamp


# Import the class to be tested


@pytest.fixture
def mock_driver():
    """Create a mock WebDriver for testing"""
    with patch('selenium.webdriver.Chrome') as mock_chrome:
        driver_mock = Mock()
        mock_chrome.return_value = driver_mock
        yield driver_mock


@pytest.fixture
def analyzer(mock_driver):
    """Create an analyzer instance with a mock driver"""
    analyzer = WebpageResponsivenessAnalyzer("https://example.com")
    analyzer.driver = mock_driver
    return analyzer


def test_check_viewport_sizes(analyzer, mock_driver):
    """Test check_viewport_sizes method"""
    # Modify to properly mock multiple execute_script calls
    mock_driver.execute_script.side_effect = [
        # For each viewport size, provide return values
        False,  # 1st size - no horizontal scroll
        False,  # 1st size - no element overflow
        False,  # 2nd size - no horizontal scroll
        False,  # 2nd size - no element overflow
        False,  # 3rd size - no horizontal scroll
        False,  # 3rd size - no element overflow
        False,  # 4th size - no horizontal scroll
        False  # 4th size - no element overflow
    ]

    # Patch time.sleep to prevent actual waiting
    with patch('time.sleep'):
        viewport_results = analyzer.check_viewport_sizes()

    assert len(viewport_results) == 4
    # Check that each viewport size is tested
    assert all(size in viewport_results for size in ['320x568', '768x1024', '1024x768', '1920x1080'])
    # Verify the results structure
    for size, result in viewport_results.items():
        assert 'has_horizontal_scroll' in result
        assert 'elements_overflow' in result


def test_check_resource_loading(analyzer, mock_driver):
    """Test check_resource_loading method"""
    # Modify mock resources to match the method's expectations
    mock_resources = [
        {
            'name': 'https://example.com/style.css',
            'duration': 50,
            'transferSize': 1024
        },
        {
            'name': 'https://example.com/script.js',
            'duration': 100,
            # Use 'size' instead of 'transferSize'
            'size': 2048
        }
    ]
    mock_driver.execute_script.return_value = mock_resources

    resource_times = analyzer.check_resource_loading()

    assert len(resource_times) == 2
    assert resource_times['https://example.com/style.css']['duration'] == 50
    # Check 'size' instead of 'transferSize'
    assert resource_times['https://example.com/style.css']['size'] == 1024
    assert resource_times['https://example.com/script.js']['duration'] == 100
    assert resource_times['https://example.com/script.js']['size'] == 0


def test_start_analysis(analyzer, mock_driver):
    """Test start_analysis method"""
    analyzer.start_analysis()
    mock_driver.get.assert_called_once_with("https://example.com")


def test_start_analysis_exception(mock_driver):
    """Test error handling in start_analysis"""
    mock_driver.get.side_effect = Exception("Connection error")

    with pytest.raises(Exception) as excinfo:
        analyzer = WebpageResponsivenessAnalyzer("https://example.com")
        analyzer.start_analysis()

    assert "Connection error" in str(excinfo.value)


def test_check_load_time(analyzer, mock_driver):
    """Test check_load_time method"""
    # Mock performance timing script
    mock_driver.execute_script.side_effect = [
        1000,  # navigationStart
        1500  # responseEnd
    ]

    load_time = analyzer.check_load_time()

    assert load_time == 500
    assert analyzer.results['load_time'] == 500
    mock_driver.get.assert_called_with("https://example.com")


def test_check_interactive_elements(analyzer, mock_driver):
    """Test check_interactive_elements method"""
    # Create mock interactive elements
    mock_elements = [
        Mock(get_attribute=lambda attr: 'button' if attr == 'type' else 'submit_btn',
             is_displayed=lambda: True,
             tag_name='button'),
        Mock(get_attribute=lambda attr: 'input' if attr == 'type' else 'email_input',
             is_displayed=lambda: True,
             tag_name='input')
    ]
    mock_driver.find_elements.return_value = mock_elements

    # Mock WebDriverWait to always return True for element clickability
    with patch('selenium.webdriver.support.ui.WebDriverWait.until', return_value=True):
        interactive_results = analyzer.check_interactive_elements()

    assert len(interactive_results) == 2
    assert 'button_submit_btn' in interactive_results
    assert interactive_results['button_submit_btn']['visible'] is True
    assert interactive_results['button_submit_btn']['clickable'] is True


def test_generate_report(analyzer):
    """Test generate_report method"""
    # Populate results manually
    analyzer.results = {
        'load_time': 500,
        'viewport_tests': {'1920x1080': {'has_horizontal_scroll': False}},
        'resource_loading': {},
        'interactive_elements': {}
    }

    report = analyzer.generate_report()

    assert report.url == "https://example.com"
    assert validate_timestamp(report.timestamp)
    assert report.results == analyzer.results


def test_run_full_analysis(analyzer, mock_driver):
    """Test run_full_analysis method"""
    # Mock all methods to return predictable results
    with patch.object(analyzer, 'check_load_time', return_value=500), \
            patch.object(analyzer, 'check_viewport_sizes', return_value={}), \
            patch.object(analyzer, 'check_resource_loading', return_value={}), \
            patch.object(analyzer, 'check_interactive_elements', return_value={}):
        analyzer.run_full_analysis()

        # Verify methods were called
        mock_driver.get.assert_called_with("https://example.com")
        mock_driver.quit.assert_called_once()


def test_cleanup(analyzer, mock_driver):
    """Test cleanup method"""
    analyzer.cleanup()
    mock_driver.quit.assert_called_once()