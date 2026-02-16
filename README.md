# MAUDE Database Explorer

Python-based web application for exploring medical device adverse event data from the FDA's MAUDE (Manufacturer and User Facility Device Experience) database.

## About the MAUDE Database

### What is MAUDE?

The MAUDE database is the FDA's **Manufacturer and User Facility Device Experience** database, a comprehensive repository of adverse event reports involving medical devices. It is the primary post-market surveillance system for medical devices in the United States.

**Official Purpose**: MAUDE collects mandatory reports of device-related:
- Deaths
- Serious injuries  
- Device malfunctions that could lead to death or serious injury

### Who Uses MAUDE?

The database serves multiple critical stakeholders:

1. **FDA Regulators** - Monitor device safety, identify trends, trigger recalls and safety alerts
2. **Healthcare Professionals** - Research device safety profiles before procurement decisions
3. **Researchers & Academics** - Study device safety trends, conduct post-market surveillance studies
4. **Medical Device Manufacturers** - Monitor competitor products, track industry-wide issues, quality assurance
5. **Law Firms & Expert Witnesses** - Investigate device-related litigation, establish precedents
6. **Insurance Companies** - Assess risk profiles for coverage decisions
7. **Patients & Advocates** - Research specific devices before procedures, understand risks
8. **Journalists & Policy Makers** - Investigate safety issues, inform public health policy

### What People Look for in MAUDE

**Common Use Cases**:

- **Safety Trend Analysis** - Are device malfunctions increasing over time?
- **Manufacturer Comparison** - Which manufacturer has fewer adverse events for similar devices?
- **Device-Specific Research** - What problems occur with Device X?
- **Competitive Intelligence** - How does our product's safety profile compare?
- **Litigation Research** - Historical patterns of adverse events for legal cases
- **Clinical Decision-Making** - Is this implant safe for my patient?
- **Recall Prediction** - Are there early warning signs of systematic issues?
- **Post-Market Surveillance** - Monitoring newly approved devices

### Database Update Frequency

- **Updates**: Weekly (typically every Wednesday)
- **Data Lag**: Reports typically appear 3-6 months after the event date
- **Mandatory Reporting Timelines**:
  - Deaths: Within 30 days
  - Serious injuries: Within 30 days  
  - Malfunctions: Within 30 days
  - Annual summaries: Due annually for baseline malfunctions

### Data Coverage & Limitations

**What's Included**:
- All mandatory manufacturer reports (MDR - Medical Device Reports)
- User facility reports (hospitals, nursing homes, etc.)
- Voluntary reports from healthcare professionals
- Device problem codes, patient outcomes, manufacturer narratives

**Important Limitations**:
- Reporting bias (serious events more likely to be reported)
- Incomplete fields (many reports have missing data)
- Unverified information (reports aren't always confirmed)
- No causality assessment (report doesn't prove device caused event)
- Duplicate reports (same event reported by multiple parties)
- Underreporting (not all adverse events are reported)

### Available Data Fields

**Currently Accessible** (in this application):
- `report_number` - Unique identifier for each report
- `event_type` - Death, Injury, Malfunction, Other
- `date_received` - When FDA received the report
- `date_of_event` - When the event occurred
- `report_source_code` - Manufacturer, User Facility, Voluntary, etc.
- `manufacturer_contact_country` - Country of manufacturer
- `device_brand_name` - Commercial brand name
- `device_generic_name` - Generic device category
- `device_manufacturer` - Manufacturer name
- `device_class` - Risk classification (I, II, III)
- `patient_sequence_number` - Patient identifier within report
- `outcome` - Death, Hospitalization, Required Intervention, etc.
- `event_description` - Narrative description of the event

**Additional Fields Available in Full Database** (not currently displayed):
- Device problem codes and descriptions
- Patient demographics (age, sex, weight)
- Removal/correction information
- Single-use flag, reprocessed status
- Remedial actions taken
- Previous use codes
- Date device manufactured
- Manufacturer received date
- Type of report designations

## Logical Data Groupings & Analysis Approaches

### 1. **By Device Risk Classification**
- **Class III** (High Risk) - Life-sustaining/supporting devices (pacemakers, ICDs)
- **Class II** (Moderate Risk) - Most medical devices (infusion pumps, surgical tools)  
- **Class I** (Low Risk) - Simple devices (bandages, tongue depressors)

### 2. **By Event Severity**
- Death reports
- Life-threatening events
- Hospitalization required
- Permanent impairment
- Required intervention
- Malfunction only

### 3. **By Device Category**
Common high-volume categories:
- **Cardiovascular devices** - Pacemakers, stents, defibrillators, heart valves
- **Orthopedic devices** - Hip/knee implants, spinal devices
- **General hospital** - Infusion pumps, ventilators, patient monitors
- **In-vitro diagnostics** - Blood glucose monitors, COVID tests
- **Surgical instruments** - Robotics, lasers, electrosurgical devices
- **Anesthesiology** - Gas delivery systems, breathing circuits

### 4. **By Manufacturer**
Tracking specific manufacturers for:
- Competitive analysis
- Quality trends over time
- Market share of adverse events

### 5. **By Time Trends**
- Monthly/quarterly trends
- Seasonal patterns
- Pre/post recall analysis
- Device lifecycle analysis (newly approved vs established)

### 6. **By Geographic Patterns**
- Manufacturer country trends
- Device problem patterns by origin

### 7. **By Report Source**
- Manufacturer reports (most comprehensive)
- User facility reports (hospital perspective)
- Voluntary reports (may indicate underreporting gaps)

## Installation & Setup

### Option 1: Web UI (Recommended)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the web interface
python maude_ui.py
```

Then open your browser to `http://localhost:8050`

### Option 2: Python API

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from maude_api_fetch import MAUDEFetcher

# Create a fetcher instance
fetcher = MAUDEFetcher()

# Simple search
results = fetcher.search('device.generic_name:"pacemaker"', limit=100)

# Convert to pandas DataFrame
df = fetcher.parse_to_dataframe(results['results'])

# Save to CSV
fetcher.save_to_csv(df, 'pacemaker_reports.csv')
```

## Search Query Examples

### Search by Device Name
```python
query = 'device.generic_name:"insulin+pump"'
```

### Search by Date Range
```python
query = 'date_received:[20230101+TO+20231231]'
```

### Search by Manufacturer
```python
query = 'device.manufacturer_d_name:"medtronic"'
```

### Search by Event Type
```python
query = 'event_type:"Death"'
```

### Complex Queries (using AND/OR)
```python
query = 'event_type:"Injury"+AND+date_received:[20230101+TO+20231231]+AND+device.generic_name:"defibrillator"'
```

## Key Features

- **Automatic Pagination**: Fetch all results across multiple API calls
- **Rate Limiting**: Built-in delays to respect API limits
- **DataFrame Conversion**: Easy conversion to pandas for analysis
- **Multiple Export Formats**: Save as CSV or JSON
- **Error Handling**: Graceful handling of API errors

## Main Methods

### `search(search_query, limit=100, skip=0)`
Fetch a single page of results.

### `fetch_all(search_query, max_results=None, delay=0.5)`
Fetch all results with automatic pagination.

### `parse_to_dataframe(results)`
Convert JSON results to pandas DataFrame.

### `save_to_csv(df, filename)`
Save DataFrame to CSV file.

### `save_to_json(results, filename)`
Save raw JSON results to file.

## DataFrame Columns

The parsed DataFrame includes:
- `report_number`: Unique report identifier
- `event_type`: Type of event (Death, Injury, Malfunction, etc.)
- `date_received`: Date FDA received the report
- `date_of_event`: Date the event occurred
- `device_brand_name`: Brand name of the device
- `device_generic_name`: Generic device type
- `device_manufacturer`: Manufacturer name
- `event_description`: Narrative description of the event
- And more...

## API Rate Limits

- **Without API key**: 240 requests per minute, 120,000 per day
- **With API key**: 1,000 requests per minute, 120,000 per day

Get a free API key at: https://open.fda.gov/apis/authentication/

## Common Search Fields

- `device.generic_name`: Generic device type
- `device.brand_name`: Brand name
- `device.manufacturer_d_name`: Manufacturer name
- `event_type`: Death, Injury, Malfunction, etc.
- `date_received`: Date in YYYYMMDD format
- `date_of_event`: Event date in YYYYMMDD format
- `report_source_code`: Source of report

## Tips

1. Use `+` instead of spaces in search queries
2. Use quotes around phrases: `"insulin+pump"`
3. Date ranges use format: `[YYYYMMDD+TO+YYYYMMDD]`
4. Use `AND`, `OR` for complex queries (must be uppercase)
5. Start with small `max_results` to test your query

## Troubleshooting 500 Errors

The FDA API can return 500 errors for overly broad queries. If you encounter this:

**❌ Don't do this:**
```python
# Too broad - entire year without filter
query = 'date_received:[20230101+TO+20231231]'
```

**✅ Do this instead:**
```python
# Add a device type to narrow results
query = 'device.generic_name:"pacemaker"+AND+date_received:[20230101+TO+20231231]'

# Or use shorter date ranges
query = 'date_received:[20240101+TO+20240131]'  # One month

# Or search by specific device/manufacturer first
query = 'device.manufacturer_d_name:"medtronic"'
```

**Working Query Patterns:**
- Device type: `device.generic_name:"pacemaker"`
- Manufacturer: `device.manufacturer_d_name:"medtronic"`
- Event type: `event_type:"Death"`
- Brand: `device.brand_name:"freestyle"`
- Recent month: `date_received:[20240101+TO+20240131]`
- Combined: `device.generic_name:"insulin+pump"+AND+event_type:"Injury"`

## Examples

See `maude_api_fetch.py` for 6 complete examples showing different use cases.

## Resources

- OpenFDA API Documentation: https://open.fda.gov/apis/device/event/
- Query Syntax: https://open.fda.gov/apis/query-syntax/
- MAUDE Database: https://www.fda.gov/medical-devices/mandatory-reporting-requirements-manufacturers-importers-and-device-user-facilities/manufacturer-and-user-facility-device-experience-maude