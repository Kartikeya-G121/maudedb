# Web UI Layout Description

## Overview
The MAUDE Database Web UI is a clean, professional interface with a two-column layout that makes it easy to search and view medical device adverse event data.

## Layout Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│                    🏥 MAUDE Database Viewer                         │
│              FDA Medical Device Adverse Event Reports               │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────┬──────────────────────────────────────────────┐
│                      │                                              │
│  SEARCH PANEL        │         RESULTS PANEL                        │
│  (Left Column)       │         (Right Column)                       │
│                      │                                              │
│ ┌──────────────────┐ │  ┌─────────────────────────────────────┐   │
│ │ Sample Queries   │ │  │ ✓ Found 247 reports! Scroll down... │   │
│ │ [Dropdown]       │ │  └─────────────────────────────────────┘   │
│ │  • Pacemaker     │ │                                              │
│ │  • Insulin Pump  │ │  ┌────────┬────────┬────────┬────────┐      │
│ │  • Death Events  │ │  │ Total  │ Event  │Devices │Manufac │      │
│ │  • Custom        │ │  │Reports │Types   │        │turers  │      │
│ └──────────────────┘ │  ├────────┼────────┼────────┼────────┤      │
│                      │  │  247   │   4    │   12   │   8    │      │
│ ┌──────────────────┐ │  └────────┴────────┴────────┴────────┘      │
│ │ Custom Query:    │ │                                              │
│ │ [Text Input]     │ │  ┌──────────────────────────────────────┐   │
│ │                  │ │  │         Search Results               │   │
│ └──────────────────┘ │  ├──────────────────────────────────────┤   │
│                      │  │ Report # │ Date   │Type  │Device    │   │
│ ┌──────────────────┐ │  ├──────────┼────────┼──────┼──────────┤   │
│ │ Max Results:     │ │  │ 1234567  │2024-01 │Injury│Pacemaker │   │
│ │ [100]            │ │  │ 1234568  │2024-01 │Death │Pacemaker │   │
│ └──────────────────┘ │  │ 1234569  │2024-01 │Malfn │Pacemaker │   │
│                      │  │   ...    │  ...   │ ...  │   ...    │   │
│ ┌──────────────────┐ │  ├──────────┴────────┴──────┴──────────┤   │
│ │[Search Database] │ │  │  Rows 1-25 of 247   [< 1 2 3 4 >]  │   │
│ └──────────────────┘ │  └──────────────────────────────────────┘   │
│                      │                                              │
│ ┌──────────────────┐ │  Table Features:                             │
│ │[Export to CSV]   │ │  • Click headers to sort                     │
│ └──────────────────┘ │  • Type to filter columns                    │
│                      │  • Use pagination controls                   │
└──────────────────────┴──────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Data source: FDA openFDA API | Query Syntax Guide                  │
└─────────────────────────────────────────────────────────────────────┘
```

## Color Scheme

- **Primary Color**: Blue (Bootstrap primary) - for main action buttons
- **Success Color**: Green - for successful search messages
- **Warning Color**: Orange - for warnings and cautions
- **Danger Color**: Red - for errors
- **Background**: White/Light gray alternating rows in table
- **Cards**: Light gray background with subtle shadows

## Component Details

### 1. Header Section
- Large centered title with hospital emoji
- Subtitle explaining the data source
- Clean typography with good spacing

### 2. Search Panel (Left Column - 4 columns wide on large screens)
Contains a single card with:
- **Sample Queries Dropdown**: Pre-built common queries
- **Custom Query Input**: Free-form text input for advanced users
- **Max Results Number Input**: Spinner control (1-5000)
- **Search Button**: Large, blue, full-width
- **Export Button**: Secondary color, initially disabled

### 3. Results Panel (Right Column - 8 columns wide on large screens)

#### Status Message Area
- Shows loading spinner during search
- Success message in green when data loads
- Warning messages in orange for no results
- Error messages in red with helpful hints

#### Statistics Cards (4 cards in a row)
Each card shows:
- Label (gray, small text)
- Large number (main statistic)
- Minimal, clean design

Cards display:
1. Total Reports (count)
2. Event Types (unique count)
3. Devices (unique count)
4. Manufacturers (unique count)

#### Data Table Card
- Clean white card with shadow
- Table with alternating row colors (white/light gray)
- Column headers in gray with bold text
- Sortable columns (click header)
- Filterable columns (type in filter row)
- Pagination controls at bottom
- Built-in export button in table

### 4. Footer
- Centered, small text
- Links to FDA resources
- Minimal, non-intrusive

## Responsive Behavior

### Desktop (Large Screens)
- Two-column layout (4/8 split)
- All features visible
- Table shows many columns

### Tablet (Medium Screens)
- Two-column layout maintained
- Table scrolls horizontally if needed
- Statistics cards stack 2x2

### Mobile (Small Screens)
- Single column (search panel on top)
- Full-width components
- Statistics cards stack vertically
- Table fully scrollable

## Interactions

### Search Flow
1. User selects sample query OR enters custom query
2. Clicks "Search Database" button
3. Loading spinner appears
4. Results load with success message
5. Statistics cards populate
6. Data table appears with results
7. Export button becomes enabled

### Table Interactions
- **Sort**: Click column header (arrow indicates direction)
- **Filter**: Type in text box below column header
- **Navigate**: Use pagination controls (< 1 2 3 >)
- **Export**: Click "Export" button in table toolbar

### Export Flow
1. After successful search, "Export to CSV" button enables
2. Click button
3. File downloads with timestamp in filename
4. Format: `maude_export_YYYYMMDD_HHMMSS.csv`

## Data Display

### Columns Shown (default)
1. Report Number
2. Date Received
3. Event Type
4. Device Generic Name
5. Device Brand Name
6. Device Manufacturer
7. Outcome

### Data Formatting
- Dates: YYYY-MM-DD format
- Empty values: Shown as empty cells
- Long text: Wraps within cell
- Numbers: Formatted with commas

## User Experience Features

### Loading States
- Spinner during API calls
- Clear status messages
- Disabled buttons during loading

### Error Handling
- Clear error messages
- Helpful suggestions (e.g., "try narrowing your search")
- Link to troubleshooting documentation

### Data Quality
- Empty/null values handled gracefully
- Date parsing with error handling
- Column filtering works on all data types

### Performance
- Pagination for large datasets
- Client-side filtering and sorting (fast)
- Configurable page size (default 25 rows)

## Accessibility
- Semantic HTML structure
- Proper heading hierarchy
- Keyboard navigation support
- Screen reader friendly labels
- Good color contrast ratios

## Technical Stack
- **Framework**: Dash (Python)
- **Styling**: Bootstrap (via dash-bootstrap-components)
- **Table**: Dash DataTable (built-in features)
- **Icons**: Bootstrap Icons (optional)
- **Layout**: Responsive grid system

## Customization Points

Users can easily customize:
1. Port number (.env file)
2. Theme (change Bootstrap theme)
3. Rows per page (ROWS_PER_PAGE in .env)
4. Display columns (edit display_columns list)
5. Sample queries (edit SAMPLE_QUERIES list)
