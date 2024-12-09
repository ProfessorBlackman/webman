import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple
import re

from dtos.responses.accessibility_response import AccessibilityAnalysisResult


class WebAccessibilityAnalyzer:
    def __init__(self, url: str):
        self.url = url
        self.soup = None
        self.issues = []

        # Define required ARIA attributes for specific roles
        self.required_aria = {
            'checkbox': ['aria-checked'],
            'combobox': ['aria-expanded'],
            'slider': ['aria-valuenow', 'aria-valuemin', 'aria-valuemax'],
            'progressbar': ['aria-valuenow', 'aria-valuemin', 'aria-valuemax'],
            'scrollbar': ['aria-controls', 'aria-valuenow', 'aria-valuemin', 'aria-valuemax'],
            'spinbutton': ['aria-valuenow', 'aria-valuemin', 'aria-valuemax'],
            'textbox': ['aria-multiline'],
        }

    def load_page(self) -> bool:
        """Loads the webpage and creates BeautifulSoup object"""
        print(f"Loading page: {self.url}")
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            self.soup = BeautifulSoup(response.text, 'html.parser')
            return True
        except Exception as e:
            self.issues.append(f"Error loading page: {str(e)}")
            return False

    def check_images_alt(self) -> List[Dict]:
        """Checks for images without alt text"""
        print("Checking images for missing alt text")
        img_issues = []
        if self.soup:
            images = self.soup.find_all('img')
            print(f"Found {len(images)} images")
            for img in images:
                if not img.get('alt'):
                    img_issues.append({
                        'element': 'img',
                        'src': img.get('src', 'unknown'),
                        'issue': 'Missing alt text'
                    })
        print(f"Found {len(img_issues)} images with missing alt text")
        return img_issues

    def check_heading_hierarchy(self) -> List[Dict]:
        """Checks for proper heading hierarchy"""
        print("Checking heading hierarchy")
        heading_issues = []
        if self.soup:
            headings = self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            current_level = 0
            for heading in headings:
                level = int(heading.name[1])
                if level - current_level > 1:
                    heading_issues.append({
                        'element': heading.name,
                        'text': heading.text.strip(),
                        'issue': f'Skipped heading level from h{current_level} to h{level}'
                    })
                current_level = level
            print(f"Found {len(heading_issues)} heading hierarchy issues")
        return heading_issues

    def check_form_labels(self) -> List[Dict]:
        """Checks for form inputs without associated labels"""
        print("Checking form labels")
        form_issues = []
        if self.soup:
            inputs = self.soup.find_all('input')
            for input_elem in inputs:
                input_id = input_elem.get('id')
                if input_id:
                    label = self.soup.find('label', {'for': input_id})
                    if not label:
                        form_issues.append({
                            'element': 'input',
                            'type': input_elem.get('type', 'unknown'),
                            'id': input_id,
                            'issue': 'Missing associated label'
                        })
        print(f"Found {len(form_issues)} form input issues")
        return form_issues

    def check_color_contrast(self) -> List[Dict]:
        """Checks for potential color contrast issues (basic check)"""
        print("Checking color contrast")
        contrast_issues = []
        if self.soup:
            elements = self.soup.find_all(['p', 'span', 'div', 'a'])
            for elem in elements:
                style = elem.get('style', '')
                if 'color' in style.lower():
                    contrast_issues.append({
                        'element': elem.name,
                        'text': elem.text.strip()[:50],
                        'issue': 'Potential color contrast issue'
                    })
        print(f"Found {len(contrast_issues)} potential color contrast issues")
        return contrast_issues

    def check_aria_attributes(self) -> List[Dict]:
        """Checks for proper ARIA attribute usage"""
        print("Checking ARIA attributes")
        aria_issues = []
        if self.soup:
            aria_issues.extend(self._check_required_aria_attributes())
            aria_issues.extend(self._check_empty_aria_labels())
            aria_issues.extend(self._check_aria_references('aria-describedby'))
            aria_issues.extend(self._check_aria_references('aria-labelledby'))
        print(f"Found {len(aria_issues)} ARIA attribute issues")
        return aria_issues

    def _check_required_aria_attributes(self) -> List[Dict]:
        """Checks for missing required ARIA attributes"""
        issues = []
        elements_with_role = self.soup.find_all(attrs={'role': True})
        for element in elements_with_role:
            role = element.get('role')
            if role in self.required_aria:
                missing_attrs = [attr for attr in self.required_aria[role] if not element.get(attr)]
                if missing_attrs:
                    issues.append({
                        'element': element.name,
                        'role': role,
                        'missing_attributes': missing_attrs,
                        'issue': f'Missing required ARIA attributes: {", ".join(missing_attrs)}'
                    })
        return issues

    def _check_empty_aria_labels(self) -> List[Dict]:
        """Checks for empty aria-label attributes"""
        issues = []
        elements_with_arialabel = self.soup.find_all(attrs={'aria-label': True})
        for element in elements_with_arialabel:
            if not element.get('aria-label').strip():
                issues.append({
                    'element': element.name,
                    'issue': 'Empty aria-label attribute'
                })
        return issues

    def _check_aria_references(self, attribute: str) -> List[Dict]:
        """Checks for invalid ARIA references"""
        issues = []
        elements_with_attribute = self.soup.find_all(attrs={attribute: True})
        for element in elements_with_attribute:
            ids = element.get(attribute).split()
            for id_ref in ids:
                if not self.soup.find(id=id_ref):
                    issues.append({
                        'element': element.name,
                        'issue': f'Invalid {attribute} reference: {id_ref}'
                    })
        return issues

    def analyze(self) -> Dict:
        """Performs complete accessibility analysis"""
        print(f"Analyzing accessibility for: {self.url}")
        if not self.load_page():
            print("Failed to load page")
            return {'error': 'Failed to load page', 'issues': self.issues}

        results = {
            'url': self.url,
            'image_issues': self.check_images_alt(),
            'heading_issues': self.check_heading_hierarchy(),
            'form_issues': self.check_form_labels(),
            'contrast_issues': self.check_color_contrast(),
            'aria_issues': self.check_aria_attributes(),
            'total_issues': 0
        }

        results['total_issues'] = (
                len(results['image_issues']) +
                len(results['heading_issues']) +
                len(results['form_issues']) +
                len(results['contrast_issues']) +
                len(results['aria_issues'])
        )

        print("Accessibility analysis complete")
        print(results)

        return AccessibilityAnalysisResult.from_dict(results)