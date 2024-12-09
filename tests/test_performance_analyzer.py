import pytest
from unittest.mock import Mock, patch

from services.performance_analyzer import WebPageAnalyzer, GOOD, NEEDS_IMPROVEMENT, POOR


@pytest.fixture
def analyzer():
    return WebPageAnalyzer()


@pytest.fixture
def mock_driver():
    with patch('selenium.webdriver.Chrome') as mock:
        driver_instance = Mock()
        mock.return_value = driver_instance
        yield driver_instance


@pytest.fixture
def mock_requests():
    with patch('requests.get') as mock:
        yield mock


class TestWebPageAnalyzer:
    def test_init(self):
        analyzer = WebPageAnalyzer()
        assert analyzer.metrics == {}
        assert '--headless' in analyzer.chrome_options.arguments
        assert '--disable-gpu' in analyzer.chrome_options.arguments

    def test_measure_ttfb(self, analyzer, mock_requests):
        with patch('time.time') as mock_time:
            mock_time.side_effect = [0, 1]  # Start time and end time
            analyzer.measure_ttfb('https://example.com')

        assert analyzer.metrics['TTFB'] == 1000.0  # 1 second = 1000ms
        mock_requests.assert_called_once_with('https://example.com')

    def test_measure_fcp_lcp(self, analyzer, mock_driver):
        mock_driver.execute_script.return_value = {'FCP': 1500, 'LCP': 2000}

        analyzer.measure_fcp_lcp('https://example.com')

        assert analyzer.metrics['FCP'] == 1500.0
        assert analyzer.metrics['LCP'] == 2000.0
        mock_driver.quit.assert_called_once()

    def test_measure_cls(self, analyzer, mock_driver):
        mock_driver.execute_script.return_value = 0.15

        analyzer.measure_cls('https://example.com')

        assert analyzer.metrics['CLS'] == 0.15
        mock_driver.quit.assert_called_once()

    def test_measure_fid(self, analyzer, mock_driver):
        mock_driver.execute_script.return_value = 50

        analyzer.measure_fid('https://example.com')

        assert analyzer.metrics['FID'] == 50.0
        mock_driver.quit.assert_called_once()

    def test_analyze_adds_https(self, analyzer):
        analyzer.metrics = {
            'TTFB': 500,
            'FCP': 1500,
            'LCP': 2000,
            'CLS': 0.05,
            'FID': 50
        }
        with patch.object(analyzer, 'measure_ttfb') as mock_ttfb, \
                patch.object(analyzer, 'measure_fcp_lcp') as mock_fcp_lcp, \
                patch.object(analyzer, 'measure_cls') as mock_cls, \
                patch.object(analyzer, 'measure_fid') as mock_fid:
            analyzer.analyze('example.com')

            expected_url = 'https://example.com'
            mock_ttfb.assert_called_once_with(expected_url)
            mock_fcp_lcp.assert_called_once_with(expected_url)
            mock_cls.assert_called_once_with(expected_url)
            mock_fid.assert_called_once_with(expected_url)

    @pytest.mark.parametrize("metric_values,expected_ratings", [
        (
                {'TTFB': 500, 'FCP': 1500, 'LCP': 2000, 'CLS': 0.05, 'FID': 50},
                {'TTFB': GOOD, 'FCP': GOOD, 'LCP': GOOD, 'CLS': GOOD, 'FID': GOOD}
        ),
        (
                {'TTFB': 1500, 'FCP': 2500, 'LCP': 3500, 'CLS': 0.2, 'FID': 200},
                {'TTFB': NEEDS_IMPROVEMENT, 'FCP': NEEDS_IMPROVEMENT, 'LCP': NEEDS_IMPROVEMENT,
                 'CLS': NEEDS_IMPROVEMENT, 'FID': NEEDS_IMPROVEMENT}
        ),
        (
                {'TTFB': 2000, 'FCP': 3500, 'LCP': 4500, 'CLS': 0.3, 'FID': 350},
                {'TTFB': POOR, 'FCP': POOR, 'LCP': POOR, 'CLS': POOR, 'FID': POOR}
        ),
    ])
    def test_get_results_ratings(self, analyzer, metric_values, expected_ratings):
        analyzer.metrics = metric_values
        results = analyzer.get_results()

        for metric, value in metric_values.items():
            assert getattr(results, metric).value == value
            assert getattr(results, metric).rating == expected_ratings[metric]
            assert getattr(results, metric).unit == ('score' if metric == 'CLS' else 'ms')

    def test_error_handling_in_measurement_methods(self, analyzer, mock_driver):
        mock_driver.get.side_effect = Exception("Browser error")

        with pytest.raises(Exception):
            analyzer.measure_fcp_lcp('https://example.com')

        mock_driver.quit.assert_called_once()