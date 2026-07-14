#!/usr/bin/env python3
"""
Quick script to embed the CSV data into the PRESET_CYCLE in cgm-tracker.html
so the heatmap works immediately without requiring a CSV upload.
"""
import json
import re

csv_path = 'manual-backups/lingo-cgm-2026-05-27-to-2026-06-07.csv'
html_path = 'cgm-tracker.html'

# Read the CSV
with open(csv_path, 'r') as f:
    csv_data = f.read()

# Escape for JavaScript string literal using template literal (backticks)
# This preserves newlines without needing escape sequences
csv_escaped = '`' + csv_data.replace('`', '\\`').replace('${', '\\${') + '`'

# Read the HTML
with open(html_path, 'r') as f:
    html = f.read()

# Find and replace the csvData: null line in PRESET_CYCLE
# Also match if it's already a string/template literal
pattern = r'(csvData:\s*)(?:null|"[^"]*"|`[^`]*`)'
replacement = f'\\1{csv_escaped}'

html_updated = re.sub(pattern, replacement, html, flags=re.DOTALL)

# Write back
with open(html_path, 'w') as f:
    f.write(html_updated)

print(f'✓ Embedded {len(csv_data)} bytes of CSV data into PRESET_CYCLE')
