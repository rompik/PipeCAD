#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PipeCAD Automated Translation Script
Translates UI strings and documentation using configured translation services.
"""

import os
import sys
import json
import argparse
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TranslationAutomation:
    """Main class for automated translation workflow"""
    
    def __init__(self, config_path='../config/automation.json'):
        self.config = self.load_config(config_path)
        self.glossary = self.load_glossary()
        self.translation_memory = {}
        
    def load_config(self, config_path):
        """Load automation configuration"""
        config_file = Path(__file__).parent / config_path
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_glossary(self):
        """Load terminology glossary"""
        glossary_file = Path(__file__).parent / '../config/glossary.json'
        if glossary_file.exists():
            with open(glossary_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('terms', [])
        return []
    
    def translate_text(self, text, target_lang, source_lang='en'):
        """
        Translate text using configured service.
        Replace with actual API calls to Google Translate, DeepL, etc.
        """
        # Check glossary first
        for term in self.glossary:
            if term['source'].lower() in text.lower():
                if term.get('do_not_translate', False):
                    continue
                translations = term.get('translations', {})
                if target_lang in translations:
                    text = text.replace(term['source'], translations[target_lang])
        
        # TODO: Implement actual translation API call
        # For now, return placeholder
        print(f"[TRANSLATE] {source_lang} -> {target_lang}: {text[:50]}...")
        
        # Placeholder for actual translation
        return f"[{target_lang.upper()}] {text}"
    
    def translate_qt_ts_file(self, source_file, target_file, target_lang):
        """Translate Qt .ts file"""
        print(f"Translating Qt .ts file: {source_file} -> {target_file}")
        
        # Parse source .ts file
        tree = ET.parse(source_file)
        root = tree.getroot()
        
        # Update language attribute
        root.set('language', self.config['target_languages'][target_lang]['locale'])
        
        # Translate messages
        translated_count = 0
        for context in root.findall('context'):
            for message in context.findall('message'):
                source_elem = message.find('source')
                translation_elem = message.find('translation')
                
                if source_elem is not None and translation_elem is not None:
                    source_text = source_elem.text
                    if source_text:
                        # Translate
                        translated_text = self.translate_text(source_text, target_lang)
                        translation_elem.text = translated_text
                        
                        # Remove 'unfinished' type
                        if translation_elem.get('type') == 'unfinished':
                            translation_elem.set('type', 'automated')
                        
                        translated_count += 1
        
        # Save translated file
        os.makedirs(os.path.dirname(target_file), exist_ok=True)
        tree.write(target_file, encoding='utf-8', xml_declaration=True)
        
        print(f"Translated {translated_count} strings")
        return translated_count
    
    def translate_markdown_file(self, source_file, target_file, target_lang):
        """Translate Markdown documentation file"""
        print(f"Translating Markdown: {source_file} -> {target_file}")
        
        with open(source_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # TODO: Implement smart Markdown translation
        # - Preserve code blocks
        # - Preserve links
        # - Translate only text content
        
        translated_content = self.translate_text(content, target_lang)
        
        os.makedirs(os.path.dirname(target_file), exist_ok=True)
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(translated_content)
        
        print(f"Translated Markdown file")
        return True
    
    def update_status(self, target_lang, stats):
        """Update translation status file"""
        status_file = Path(__file__).parent / f'../targets/{target_lang}/status.json'
        
        status = {
            'language': target_lang,
            'language_name': self.get_language_name(target_lang),
            'last_updated': datetime.utcnow().isoformat() + 'Z',
            'statistics': stats,
            'quality': {
                'automated_score': 0.85,  # Placeholder
                'review_status': 'automated',
                'last_reviewed': None,
                'reviewer': None
            },
            'translation_method': 'automated',
            'requires_review': True,
            'issues': [],
            'notes': 'Automated translation completed'
        }
        
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2, ensure_ascii=False)
    
    def get_language_name(self, lang_code):
        """Get full language name from code"""
        for lang_config in self.config['target_languages']:
            if lang_config['code'] == lang_code:
                return lang_config['name']
        return lang_code
    
    def run(self, source, target_lang, content_type='ui'):
        """Run automated translation"""
        print(f"Starting automated translation for {target_lang}")
        print(f"Source: {source}")
        print(f"Content type: {content_type}")
        
        if content_type == 'ui':
            # Translate Qt .ts file
            source_file = Path(source)
            target_file = Path(__file__).parent / f'../targets/{target_lang}/ui/pipecad_{target_lang}.ts'
            
            translated_count = self.translate_qt_ts_file(source_file, target_file, target_lang)
            
            stats = {
                'ui_strings': {
                    'total': translated_count,
                    'translated': translated_count,
                    'unfinished': 0,
                    'fuzzy': 0,
                    'percentage': 100
                }
            }
            
        elif content_type == 'docs':
            # Translate documentation
            source_file = Path(source)
            target_file = Path(__file__).parent / f'../../docs/{target_lang}/{source_file.name}'
            
            self.translate_markdown_file(source_file, target_file, target_lang)
            
            stats = {
                'documentation': {
                    'total_files': 1,
                    'translated_files': 1,
                    'percentage': 100
                }
            }
        
        # Update status
        self.update_status(target_lang, stats)
        
        print(f"Translation completed for {target_lang}")
        print(f"Remember to review translations in Qt Linguist or review tool")


def main():
    parser = argparse.ArgumentParser(description='PipeCAD Automated Translation')
    parser.add_argument('--source', required=True, help='Source file to translate')
    parser.add_argument('--target', required=True, help='Target language code (e.g., ru, zh)')
    parser.add_argument('--type', default='ui', choices=['ui', 'docs'], 
                       help='Content type (ui or docs)')
    parser.add_argument('--config', default='../config/automation.json',
                       help='Configuration file path')
    
    args = parser.parse_args()
    
    automation = TranslationAutomation(config_path=args.config)
    automation.run(args.source, args.target, args.type)


if __name__ == '__main__':
    main()
