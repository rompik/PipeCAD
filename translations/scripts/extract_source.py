#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PipeCAD Source String Extraction Script
Extracts translatable strings from Python source code into Qt .ts format.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path


def extract_qt_strings(source_dir, output_file):
    """
    Extract Qt translatable strings from Python source code.
    Uses pylupdate or pyside-lupdate to generate .ts file.
    """
    print(f"Extracting Qt strings from: {source_dir}")
    print(f"Output file: {output_file}")
    
    source_path = Path(source_dir)
    output_path = Path(output_file)
    
    # Find all Python files
    py_files = list(source_path.glob('**/*.py'))
    
    if not py_files:
        print("No Python files found!")
        return False
    
    print(f"Found {len(py_files)} Python files")
    
    # Create output directory
    os.makedirs(output_path.parent, exist_ok=True)
    
    # Try different lupdate tools
    lupdate_tools = [
        'pylupdate5',
        'pyside2-lupdate',
        'pyside6-lupdate',
        'lupdate'
    ]
    
    lupdate_found = None
    for tool in lupdate_tools:
        try:
            result = subprocess.run([tool, '-version'], 
                                  capture_output=True, 
                                  text=True)
            if result.returncode == 0:
                lupdate_found = tool
                print(f"Using {tool}")
                break
        except FileNotFoundError:
            continue
    
    if not lupdate_found:
        print("Warning: No lupdate tool found. Generating basic .ts template.")
        generate_basic_ts_template(py_files, output_path)
        return True
    
    # Create project file for lupdate
    pro_file = output_path.parent / 'temp.pro'
    
    with open(pro_file, 'w', encoding='utf-8') as f:
        f.write('SOURCES = \\\n')
        for py_file in py_files:
            f.write(f'    {py_file.as_posix()} \\\n')
        f.write(f'\nTRANSLATIONS = {output_path.name}\n')
    
    # Run lupdate
    result = subprocess.run([lupdate_found, str(pro_file)],
                          capture_output=True,
                          text=True,
                          cwd=output_path.parent)
    
    if result.returncode != 0:
        print(f"Error running {lupdate_found}:")
        print(result.stderr)
        # Try manual extraction as fallback
        generate_basic_ts_template(py_files, output_path)
    
    # Cleanup
    if pro_file.exists():
        pro_file.unlink()
    
    print(f"Extraction complete: {output_path}")
    return True


def generate_basic_ts_template(py_files, output_path):
    """Generate a basic .ts template by parsing Python files for QT_TRANSLATE_NOOP"""
    import re
    
    print("Generating basic .ts template from source code...")
    
    strings = []
    
    # Pattern to find QT_TRANSLATE_NOOP calls
    pattern = r'QT_TRANSLATE_NOOP\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)'
    
    for py_file in py_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                matches = re.findall(pattern, content)
                for context, text in matches:
                    strings.append({
                        'context': context,
                        'source': text,
                        'location': str(py_file.relative_to(py_file.parents[2]))
                    })
        except Exception as e:
            print(f"Error reading {py_file}: {e}")
    
    print(f"Found {len(strings)} translatable strings")
    
    # Generate .ts XML
    xml_content = generate_ts_xml(strings)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    
    print(f"Generated template: {output_path}")


def generate_ts_xml(strings):
    """Generate Qt .ts XML format"""
    xml = '<?xml version="1.0" encoding="utf-8"?>\n'
    xml += '<!DOCTYPE TS>\n'
    xml += '<TS version="2.1" language="en_US">\n'
    
    # Group by context
    contexts = {}
    for item in strings:
        context = item['context']
        if context not in contexts:
            contexts[context] = []
        contexts[context].append(item)
    
    for context, items in contexts.items():
        xml += f'<context>\n'
        xml += f'    <name>{context}</name>\n'
        for item in items:
            xml += '    <message>\n'
            xml += f'        <location filename="{item["location"]}" line="0"/>\n'
            xml += f'        <source>{escape_xml(item["source"])}</source>\n'
            xml += '        <translation type="unfinished"></translation>\n'
            xml += '    </message>\n'
        xml += '</context>\n'
    
    xml += '</TS>\n'
    return xml


def escape_xml(text):
    """Escape special XML characters"""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&apos;'))


def main():
    parser = argparse.ArgumentParser(description='Extract PipeCAD Source Strings')
    parser.add_argument('--source', required=True, 
                       help='Source directory containing Python files')
    parser.add_argument('--output', required=True,
                       help='Output .ts file path')
    
    args = parser.parse_args()
    
    success = extract_qt_strings(args.source, args.output)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
