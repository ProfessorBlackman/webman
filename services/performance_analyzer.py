import time
from urllib.parse import urlparse

import requests
from selenium import webdriver

from dtos.responses.performance_response import WebVitalsResult

POOR = 'Poor'

GOOD = 'Good'

NEEDS_IMPROVEMENT = 'Needs Improvement'


class WebPageAnalyzer:
    def __init__(self):
        self.metrics = {}
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--disable-gpu')

    def measure_ttfb(self, url):
        """Measure Time to First Byte (TTFB)"""
        print(f"Measuring TTFB for {url}")
        start_time = time.time()
        requests.get(url)
        ttfb = (time.time() - start_time) * 1000  # Convert to milliseconds
        self.metrics['TTFB'] = round(ttfb, 2)
        print(f"TTFB: {self.metrics['TTFB']} ms")

    def measure_fcp_lcp(self, url):
        """Measure First Contentful Paint (FCP) and Largest Contentful Paint (LCP)"""
        print(f"Measuring FCP and LCP for {url}")
        driver = webdriver.Chrome(options=self.chrome_options)
        try:
            driver.get(url)

            # Execute JavaScript to get FCP and LCP
            script = """
                return new Promise((resolve) => {
                    const observer = new PerformanceObserver((list) => {
                        const entries = list.getEntries();
                        const metrics = {};

                        entries.forEach(entry => {
                            if (entry.entryType === 'paint' && entry.name === 'first-contentful-paint') {
                                metrics.FCP = entry.startTime;
                            }
                            if (entry.entryType === 'largest-contentful-paint') {
                                metrics.LCP = entry.startTime;
                            }
                        });

                        resolve(metrics);
                    });

                    observer.observe({
                        entryTypes: ['paint', 'largest-contentful-paint']
                    });

                    // Timeout after 10 seconds
                    setTimeout(() => resolve({}), 10000);
                });
            """

            metrics = driver.execute_script(script)
            self.metrics['FCP'] = round(metrics.get('FCP', 0), 2)
            self.metrics['LCP'] = round(metrics.get('LCP', 0), 2)

        finally:
            driver.quit()

        print(f"FCP: {self.metrics['FCP']} ms")
        print(f"LCP: {self.metrics['LCP']} ms")

    def measure_cls(self, url):
        """Measure Cumulative Layout Shift (CLS)"""
        print(f"Measuring CLS for {url}")
        driver = webdriver.Chrome(options=self.chrome_options)
        try:
            driver.get(url)

            script = """
                return new Promise((resolve) => {
                    let cls = 0;

                    new PerformanceObserver((list) => {
                        for (const entry of list.getEntries()) {
                            if (!entry.hadRecentInput) {
                                cls += entry.value;
                            }
                        }
                    }).observe({entryTypes: ['layout-shift']});

                    setTimeout(() => resolve(cls), 5000);
                });
            """

            cls = driver.execute_script(script)
            self.metrics['CLS'] = round(cls, 3)

        finally:
            driver.quit()

        print(f"CLS: {self.metrics['CLS']}")

    def measure_fid(self, url):
        """Measure First Input Delay (FID)"""
        print(f"Measuring FID for {url}")
        driver = webdriver.Chrome(options=self.chrome_options)
        try:
            driver.get(url)

            script = """
                return new Promise((resolve) => {
                    new PerformanceObserver((list) => {
                        const entries = list.getEntries();
                        if (entries.length > 0) {
                            resolve(entries[0].processingStart - entries[0].startTime);
                        }
                    }).observe({entryTypes: ['first-input']});

                    setTimeout(() => resolve(0), 5000);
                });
            """

            fid = driver.execute_script(script)
            self.metrics['FID'] = round(fid, 2)

        finally:
            driver.quit()

        print(f"FID: {self.metrics['FID']} ms")

    def analyze(self, url: str) -> WebVitalsResult:
        """Analyze all web vitals metrics for a given URL
        :param url:
        :return: WebVitalsResult
        """
        print(f"Analyzing site: {url}")
        if not urlparse(url).scheme:
            url = 'https://' + url

        self.measure_ttfb(url)
        self.measure_fcp_lcp(url)
        self.measure_cls(url)
        self.measure_fid(url)

        return self.get_results()

    def get_results(self) -> WebVitalsResult:
        """Return analysis results with ratings"""
        print("Generating analysis results")
        ratings = {
            'TTFB': {
                GOOD: lambda x: x < 800,
                NEEDS_IMPROVEMENT: lambda x: x < 1800,
                POOR: lambda x: x >= 1800
            },
            'FCP': {
                GOOD: lambda x: x < 1800,
                NEEDS_IMPROVEMENT: lambda x: x < 3000,
                POOR: lambda x: x >= 3000
            },
            'LCP': {
                GOOD: lambda x: x < 2500,
                NEEDS_IMPROVEMENT: lambda x: x < 4000,
                POOR: lambda x: x >= 4000
            },
            'CLS': {
                GOOD: lambda x: x < 0.1,
                NEEDS_IMPROVEMENT: lambda x: x < 0.25,
                POOR: lambda x: x >= 0.25
            },
            'FID': {
                GOOD: lambda x: x < 100,
                NEEDS_IMPROVEMENT: lambda x: x < 300,
                POOR: lambda x: x >= 300
            }
        }

        results = {}
        for metric, value in self.metrics.items():
            rating = POOR
            for rating_level, check in ratings[metric].items():
                if check(value):
                    rating = rating_level
                    break

            results[metric] = {
                'value': value,
                'rating': rating,
                'unit': 'ms' if metric != 'CLS' else 'score'
            }

        return WebVitalsResult.from_dict(results)