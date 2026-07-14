#!/usr/bin/env python3
"""
Update PRESET_CYCLE in cgm-tracker.html with context data from JSON file.
Adds meals, exercise, and contextNotes to the daily array.
"""
import json
import re

json_path = 'manual-backups/cgm-2026-05-27-to-2026-06-07 (2).json'
html_path = 'cgm-tracker.html'

# Read the JSON with context data
with open(json_path, 'r') as f:
    context_data = json.load(f)

# Read the HTML
with open(html_path, 'r') as f:
    html = f.read()

# Build the daily array with context data
daily_with_context = []
for day in context_data['stats']['daily']:
    date = day['date']
    n = day['n']
    mean = day['mean']
    min_val = day['min']
    max_val = day['max']
    tir = day['tir']
    pct_low = day['pctLow']
    pct_high = day['pctHigh']
    
    # Escape single quotes in text fields
    meals = day.get('meals', '').replace("'", "\\'").replace('\n', '\\n')
    exercise = day.get('exercise', '').replace("'", "\\'").replace('\n', '\\n')
    context_notes = day.get('contextNotes', '').replace("'", "\\'").replace('\n', '\\n')
    
    daily_entry = f"      {{ date:'{date}', n:{n}, mean:{mean}, min:{min_val}, max:{max_val}, tir:{tir}, pctLow:{pct_low}, pctHigh:{pct_high}"
    
    # Add optional context fields if they exist
    if meals:
        daily_entry += f", meals:'{meals}'"
    if exercise:
        daily_entry += f", exercise:'{exercise}'"
    if context_notes:
        daily_entry += f", contextNotes:'{context_notes}'"
    
    daily_entry += " }"
    daily_with_context.append(daily_entry)

daily_js = ',\n'.join(daily_with_context)

# Find and replace the daily array in PRESET_CYCLE
# Look for the daily array within PRESET_CYCLE
pattern = r"(const PRESET_CYCLE = \{.*?daily: \[)(.*?)(\n    \]\s*\},\s*csvData:)"

def replacement(match):
    return match.group(1) + '\n' + daily_js + '\n    ' + match.group(3)

html_updated = re.sub(pattern, replacement, html, flags=re.DOTALL)

# Write back
with open(html_path, 'w') as f:
    f.write(html_updated)

print(f'✓ Updated PRESET_CYCLE with context data from {len(context_data["stats"]["daily"])} days')
print(f'✓ Added meals, exercise, and contextNotes fields')
