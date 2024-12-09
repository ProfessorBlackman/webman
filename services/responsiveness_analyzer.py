import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from dtos.responses.responsiveness_response import WebpageResponsivenessReport


class WebpageResponsivenessAnalyzer:
    def __init__(self, url):
        self.url = url
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.results = {}

    def start_analysis(self):
        """Initialize the analysis process"""
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.driver.get(self.url)

    def check_load_time(self):
        """Measure initial page load time"""
        time.time()
        self.driver.get(self.url)
        navigation_start = self.driver.execute_script("return window.performance.timing.navigationStart")
        response_end = self.driver.execute_script("return window.performance.timing.responseEnd")
        page_load_time = response_end - navigation_start
        self.results['load_time'] = page_load_time
        return page_load_time

    def check_viewport_sizes(self):
        """Test page rendering at different viewport sizes"""
        viewport_sizes = [
            (320, 568),  # Mobile
            (768, 1024),  # Tablet
            (1024, 768),  # Landscape tablet
            (1920, 1080)  # Desktop
        ]

        viewport_results = {}
        for width, height in viewport_sizes:
            self.driver.set_window_size(width, height)
            time.sleep(1)  # Allow page to adjust

            # Check for horizontal scrollbar
            has_horizontal_scroll = self.driver.execute_script(
                "return document.documentElement.scrollWidth > document.documentElement.clientWidth"
            )

            # Check if elements maintain proper layout
            elements_overflow = self.driver.execute_script(
                "return Array.from(document.getElementsByTagName('*')).some(el => el.offsetWidth > window.innerWidth)"
            )

            viewport_results[f"{width}x{height}"] = {
                "has_horizontal_scroll": has_horizontal_scroll,
                "elements_overflow": elements_overflow
            }

        self.results['viewport_tests'] = viewport_results
        return viewport_results

    def check_resource_loading(self):
        """Analyze resource loading performance"""
        performance_timing = self.driver.execute_script(
            "return window.performance.getEntriesByType('resource')"
        )

        resource_times = {}
        for entry in performance_timing:
            resource_times[entry['name']] = {
                'duration': entry['duration'],
                'size': entry['transferSize'] if 'transferSize' in entry else 0
            }

        self.results['resource_loading'] = resource_times
        return resource_times

    def check_interactive_elements(self):
        """Test responsiveness of interactive elements"""
        interactive_elements = self.driver.find_elements(
            by=By.CSS_SELECTOR,
            value='button, a, input, select, textarea'
        )

        interactive_results = {}
        for element in interactive_elements:
            try:
                element_type = element.get_attribute('type') or element.tag_name
                element_id = element.get_attribute('id') or element.get_attribute('class')

                # Check if element is visible and clickable
                is_visible = element.is_displayed()
                is_clickable = WebDriverWait(self.driver, 1).until(
                    EC.element_to_be_clickable(element)
                ) is not None

                interactive_results[f"{element_type}_{element_id}"] = {
                    "visible": is_visible,
                    "clickable": is_clickable
                }
            except:
                continue

        self.results['interactive_elements'] = interactive_results
        return interactive_results

    def generate_report(self):
        """Generate a comprehensive report of all analysis results"""
        report = {
            "url": self.url,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": self.results
        }

        return WebpageResponsivenessReport.from_dict(report)

    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'driver'):
            self.driver.quit()

    def run_full_analysis(self):
        """Run all analysis methods and generate report"""
        try:
            self.start_analysis()
            self.check_load_time()
            self.check_viewport_sizes()
            self.check_resource_loading()
            self.check_interactive_elements()
            return self.generate_report()
        finally:
            self.cleanup()

# Usage example:
# analyzer = WebpageResponsivenessAnalyzer("https://example.com")
# report = analyzer.run_full_analysis()
# print(report)