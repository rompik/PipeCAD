#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PipeCAD Translation Status Sync Script
Updates translation status metadata for all target languages.
"""

import os
import sys
import json
import argparse
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


class StatusSync:
    """Synchronize translation status across all languages"""
    
    def __init__(self, translations_root):
        self.root = Path(translations_root)
        self.targets_dir = self.root / 'targets'
    
    def analyze_qt_ts_file(self, ts_file):
        """Analyze Qt .ts file and return statistics"""
        if not ts_file.exists():
            return {
                'total': 0,
                'translated': 0,
                'unfinished': 0,
                'fuzzy': 0,
                'percentage': 0
            }
        
        tree = ET.parse(ts_file)
        root = tree.getroot()
        
        total = 0
        translated = 0
        unfinished = 0
        fuzzy = 0
        
        for context in root.findall('context'):
            for message in context.findall('message'):
                translation = message.find('translation')
                if translation is not None:
                    total += 1
                    trans_type = translation.get('type', '')
                    
                    if trans_type == 'unfinished':
                        unfinished += 1
                    elif trans_type == 'fuzzy':
                        fuzzy += 1
                    elif translation.text:
                        translated += 1
        
        percentage = (translated / total * 100) if total > 0 else 0
        
        return {
            'total': total,
            'translated': translated,
            'unfinished': unfinished,
            'fuzzy': fuzzy,
            'percentage': round(percentage, 2)
        }
    
    def analyze_docs_directory(self, docs_dir):
        """Analyze documentation directory and return statistics"""
        if not docs_dir.exists():
            return {
                'total_files': 0,
                'translated_files': 0,
                'percentage': 0
            }
        
        md_files = list(docs_dir.glob('**/*.md'))
        total_files = len(md_files)
        
        # Count non-empty files as translated
        translated_files = sum(1 for f in md_files if f.stat().st_size > 0)
        
        percentage = (translated_files / total_files * 100) if total_files > 0 else 0
        
        return {
            'total_files': total_files,
            'translated_files': translated_files,
            'percentage': round(percentage, 2)
        }
    
    def update_language_status(self, lang_code):
        """Update status for a specific language"""
        lang_dir = self.targets_dir / lang_code
        status_file = lang_dir / 'status.json'
        
        # Load existing status or create new
        if status_file.exists():
            with open(status_file, 'r', encoding='utf-8') as f:
                status = json.load(f)
        else:
            status = {
                'language': lang_code,
                'language_name': lang_code.upper()
            }
        
        # Analyze UI strings
        ui_file = lang_dir / 'ui' / f'pipecad_{lang_code}.ts'
        ui_stats = self.analyze_qt_ts_file(ui_file)
        
        # Analyze documentation
        docs_dir = self.root.parent / 'docs' / lang_code
        docs_stats = self.analyze_docs_directory(docs_dir)
        
        # Update status
        status['last_updated'] = datetime.utcnow().isoformat() + 'Z'
        status['statistics'] = {
            'ui_strings': ui_stats,
            'documentation': docs_stats
        }
        
        # Determine review status
        if ui_stats['percentage'] >= 95 and docs_stats['percentage'] >= 90:
            review_status = 'ready_for_review'
        elif ui_stats['percentage'] >= 50:
            review_status = 'in_progress'
        else:
            review_status = 'pending'
        
        if 'quality' not in status:
            status['quality'] = {}
        
        status['quality']['review_status'] = review_status
        
        # Save updated status
        os.makedirs(lang_dir, exist_ok=True)
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2, ensure_ascii=False)
        
        print(f"Updated status for {lang_code}:")
        print(f"  UI: {ui_stats['translated']}/{ui_stats['total']} ({ui_stats['percentage']}%)")
        print(f"  Docs: {docs_stats['translated_files']}/{docs_stats['total_files']} ({docs_stats['percentage']}%)")
        print(f"  Status: {review_status}")
        
        return status
    
    def sync_all(self):
        """Sync status for all target languages"""
        if not self.targets_dir.exists():
            print(f"Targets directory not found: {self.targets_dir}")
            return
        
        # Get all language directories
        lang_dirs = [d for d in self.targets_dir.iterdir() if d.is_dir()]
        
        print(f"Syncing status for {len(lang_dirs)} languages...")
        
        summary = []
        for lang_dir in lang_dirs:
            lang_code = lang_dir.name
            status = self.update_language_status(lang_code)
            summary.append(status)
        
        # Generate summary report
        print("\n=== Translation Status Summary ===")
        for status in summary:
            lang = status['language']
            ui_pct = status['statistics']['ui_strings']['percentage']
            docs_pct = status['statistics']['documentation']['percentage']
            review = status['quality']['review_status']
            print(f"{lang}: UI {ui_pct}% | Docs {docs_pct}% | {review}")


def main():
    parser = argparse.ArgumentParser(description='Sync PipeCAD Translation Status')
    parser.add_argument('--language', help='Specific language to update')
    parser.add_argument('--all', action='store_true', help='Update all languages')
    parser.add_argument('--root', default='.',
                       help='Translations root directory')
    
    args = parser.parse_args()
    
    sync = StatusSync(args.root)
    
    if args.all or not args.language:
        sync.sync_all()
    else:
        sync.update_language_status(args.language)


if __name__ == '__main__':
    main()
