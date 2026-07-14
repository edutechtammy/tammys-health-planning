# CGM Heatmap Visualization

## What Was Added

A **D3.js-powered daily glucose heatmap** has been integrated into the CGM Tracker page. This visualization shows hour-by-hour glucose patterns across all days in a cycle.

## Features

### Visual Design
- **Grid Layout**: Days on Y-axis (MM/DD format), hours (00:00-23:00) on X-axis
- **Color Coding**: 
  - Red → Orange (55-80 mg/dL): Hypoglycemic range
  - Orange → Green (80-110 mg/dL): Optimal range
  - Green → Yellow (110-180 mg/dL): Elevated range
- **Interactive Tooltips**: Hover over any cell to see:
  - Date and hour
  - Average glucose for that time slot
  - Number of readings

### What It Reveals
1. **Consistent Spike Windows**: Easily spot if morning spikes always occur 8-10am
2. **Overnight Patterns**: See if glucose consistently drops 3-6am (no dawn phenomenon)
3. **Hypoglycemia Clusters**: Identify specific time periods prone to lows
4. **Day-of-Week Trends**: Compare weekdays vs weekends at a glance

## Technical Implementation

### Libraries Used
- **D3.js v7.9.0**: For SVG rendering, scales, and interactivity
- **Chart.js v4.4.2**: Retained for the comparison line chart

### Key Functions
- `renderHeatmap(cycle)`: Main rendering function
- `parseCSVData(csvText)`: Parses Lingo CSV format
- `parseLocalDT(timestamp)`: Extracts date and hour from ISO timestamps

### Data Flow
1. CSV data is stored in `cycle.csvData` when importing
2. Data is parsed into a matrix: `[date][hour] = [glucose values]`
3. Mean glucose is calculated for each hour-of-day cell
4. D3 renders cells with color scale based on mean values

## File Changes

### cgm-tracker.html
- Added D3.js CDN link in `<head>`
- Added `.heatmap-*` CSS classes for styling
- Added `#heatmap-container` div after cycle detail section
- Added `renderHeatmap()` function (~150 lines)
- Modified `selectCycle()` to call `renderHeatmap()`
- Modified cycle import to store `csvData` property
- Added CSV data to `PRESET_CYCLE` via Python script

### Helper Scripts
- `_embed_csv_in_preset.py`: Embeds CSV into HTML for immediate demo

## Usage

1. **View Preset Data**: Cycle 1 already has CSV data embedded — heatmap renders immediately
2. **Import New Cycle**: When uploading a CSV via "Import New Cycle", the heatmap automatically renders
3. **Switch Cycles**: Click any cycle card to see its heatmap

## Next Steps (Potential Enhancements)

### PRIORITY: Before Next CGM Cycle (Cycle 2)

#### 1. **Context Data Indicators on Heatmap Cells** 🎯 HIGH PRIORITY
- **Feature**: Add visual indicators (dots/icons) in heatmap cells when context data is logged
- **Indicators**:
  - 🍽️ Small dot/icon when meal data is logged for that hour
  - 💊 Icon when supplements are logged
  - 🏃 Icon when exercise is logged
  - Combined indicator when multiple types exist
- **Benefit**: Instantly see which glucose patterns have detailed context vs. which are unexplained
- **Implementation**: 
  - Read from daily context log table (meals, exercise, contextNotes fields)
  - Parse timestamps to match hour slots
  - Overlay small SVG circles or text icons on heatmap cells
  - Click cell to jump to/highlight that entry in the context log below

#### 2. **Enhanced Context Log - Timestamp Precision**
- **Current**: Context log is by date only
- **Needed**: Add time-of-day fields for meals, supplements, exercise
- **Benefit**: Enables accurate hour-matching with heatmap cells
- **Format**: "08:15 Breakfast + ACV", "13:30 Walk 15min", "19:45 Magnesium"

#### 3. **Heatmap Cell Click → Context Panel**
- **Feature**: Click any heatmap cell to open a detail panel showing:
  - All glucose readings in that hour (raw values)
  - Logged meals at/near that time
  - Supplements taken
  - Exercise activity
  - Any notes from that day
- **Benefit**: Deep-dive into specific patterns without scrolling

### Future Enhancements (Post-Cycle 2)

### 1. Zoomable Timeline with Meal Annotations
- Pan/zoom glucose curve with `d3.zoom()`
- Overlay meal/exercise markers from daily context log
- Click markers to see logged notes

### 2. Circadian Rhythm Chart
- Aggregate all readings by hour-of-day (e.g., all 8am readings)
- Plot as radial/polar chart or 24-hour line with confidence bands
- Shows typical glucose curve independent of specific dates

### 3. Distribution Comparisons (Violin Plots)
- Compare glucose distributions across cycles
- See if later cycles shift the entire distribution left (tighter control)

### 4. Spike/Hypo Explorer
- Scatter plot: X=time of day, Y=glucose, color=event type
- Hover to see meal/exercise context from the context log
- Voronoi overlay for nearest-point detection

## Browser Compatibility
- Modern browsers with ES6+ support
- SVG rendering required for D3 visualizations
- Tested in Chrome, Safari, Firefox

---

**Created**: July 13, 2026  
**D3.js Version**: 7.9.0  
**Chart.js Version**: 4.4.2
