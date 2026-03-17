#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PipeCAD Translation Validation Script
Validates translation files for formatting, completeness, and quality issues.
"""

import os
import sys
import json
import argparse
import xml.etree.ElementTree as ET
import re
from pathlib import Path


class TranslationValidator:
    """Validate translation files for common issues"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.glossary = self.load_glossary()
    
    def load_glossary(self):
        """Load terminology glossary"""
        glossary_file = Path(__file__).parent / '../config/glossary.json'
        if glossary_file.exists():
            with open(glossary_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {term['source']: term for term in data.get('terms', [])}
        return {}
    
    def validate_qt_ts_file(self, ts_file):
        """Validate Qt .ts translation file"""
        print(f"Validating Qt .ts file: {ts_file}")
        
        if not ts_file.exists():
            self.issues.append(f"File not found: {ts_file}")
            return False
        
        try:
            tree = ET.parse(ts_file)
            root = tree.getroot()
        except ET.ParseError as e:
            self.issues.append(f"XML parse error: {e}")
            return False
        
        lang_code = root.get('language', '')
        if not lang_code:
            self.warnings.append("Missing language attribute in root element")
        
        # Validate messages
        for context in root.findall('context'):
            context_name = context.find('name')
            context_name_text = context_name.text if context_name is not None else 'Unknown'
            
            for message in context.findall('message'):
                source_elem = message.find('source')
                translation_elem = message.find('translation')
                
                if source_elem is None:
                    self.issues.append(f"Missing source element in context {context_name_text}")
                    continue
                
                if translation_elem is None:
                    self.issues.append(f"Missing translation element in context {context_name_text}")
                    continue
                
                source_text = source_elem.text or ''
                translation_text = translation_elem.text or ''
                
                # Check for unfinished translations
                if translation_elem.get('type') == 'unfinished':
                    self.warnings.append(f"Unfinished translation: '{source_text[:50]}...'")
                
                # Check for empty translations
                if not translation_text and source_text:
                    self.warnings.append(f"Empty translation for: '{source_text[:50]}...'")
                
                # Validate placeholders
                self.validate_placeholders(source_text, translation_text, context_name_text)
                
                # Validate HTML tags
                self.validate_html_tags(source_text, translation_text, context_name_text)
                
                # Check glossary compliance
                self.check_glossary(translation_text, lang_code, context_name_text)
        
        return len(self.issues) == 0
    
    def validate_placeholders(self, source, translation, context):
        """Validate that placeholders match between source and translation"""
        # Qt placeholders: %1, %2, etc. or %s, %d, etc.
        placeholder_pattern = r'%[0-9sd]'
        
        source_placeholders = set(re.findall(placeholder_pattern, source))
        translation_placeholders = set(re.findall(placeholder_pattern, translation))
        
        if source_placeholders != translation_placeholders:
            self.issues.append(
                f"Placeholder mismatch in {context}: "
                f"source has {source_placeholders}, translation has {translation_placeholders}"
            )
        
        # Python format placeholders: {0}, {1}, etc.
        python_pattern = r'\{[0-9]+\}'
        source_py = set(re.findall(python_pattern, source))
        translation_py = set(re.findall(python_pattern, translation))
        
        if source_py != translation_py:
            self.issues.append(
                f"Python format placeholder mismatch in {context}: "
                f"source has {source_py}, translation has {translation_py}"
            )
    
    def validate_html_tags(self, source, translation, context):
        """Validate that HTML tags are preserved"""
        tag_pattern = r'<[^>]+>'
        
        source_tags = re.findall(tag_pattern, source)
        translation_tags = re.findall(tag_pattern, translation)
        
        if len(source_tags) != len(translation_tags):
            self.warnings.append(
                f"HTML tag count mismatch in {context}: "
                f"source has {len(source_tags)}, translation has {len(translation_tags)}"
            )
    
    def check_glossary(self, translation, lang_code, context):
        """Check if translation follows glossary terms"""
        for source_term, term_data in self.glossary.items():
            if term_data.get('do_not_translate', False):
                # These terms should appear as-is
                if source_term in translation.lower():
                    continue
            else:
                # Check if correct translation is used
                translations = term_data.get('translations', {})
                if lang_code in translations:
                    expected = translations[lang_code]
                    if source_term.lower() in translation.lower():
                        if expected.lower() not in translation.lower():
                            self.warnings.append(
                                f"Glossary term '{source_term}' should be translated as '{expected}' "
                                f"in {context}"
                            )
    
    def validate_markdown_file(self, md_file):
        """Validate Markdown documentation file"""
        print(f"Validating Markdown file: {md_file}")
        
        if not md_file.exists():
            self.issues.append(f"File not found: {md_file}")
            return False
        
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for broken links
        link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        links = re.findall(link_pattern, content)
        
        for link_text, link_url in links:
            if link_url.startswith('http'):
                continue  # Skip external links
            
            # Check if local file exists
            if link_url.startswith('/'):
                link_path = Path(link_url.lstrip('/'))
            else:
                link_path = md_file.parent / link_url
            
            # Remove anchor
            link_path = str(link_path).split('#')[0]
            
            if not Path(link_path).exists():
                self.warnings.append(f"Broken link in {md_file.name}: {link_url}")
        
        # Check for untranslated code blocks (shouldn't have [LANG] markers)
        if re.search(r'\[([A-Z]{2})\]', content):
            self.warnings.append(f"Possible untranslated content markers found in {md_file.name}")
        
        return len(self.issues) == 0
    
    def report(self):
        """Generate validation report"""
        print("\n=== Validation Report ===")
        
        if not self.issues and not self.warnings:
            print("✓ All validations passed!")
            return True
        
        if self.issues:
            print(f"\n❌ {len(self.issues)} Issues Found:")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")
        
        if self.warnings:
            print(f"\n⚠ {len(self.warnings)} Warnings:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        return len(self.issues) == 0


def main():
    parser = argparse.ArgumentParser(description='Validate PipeCAD Translations')
    parser.add_argument('--file', required=True, help='Translation file to validate')
    parser.add_argument('--type', default='ui', choices=['ui', 'docs'],
                       help='File type (ui or docs)')
    
    args = parser.parse_args()
    
    validator = TranslationValidator()
    
    file_path = Path(args.file)
    
    if args.type == 'ui':
        success = validator.validate_qt_ts_file(file_path)
    else:
        success = validator.validate_markdown_file(file_path)
    
    validator.report()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
