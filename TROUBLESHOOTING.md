# MAUDE API Troubleshooting Guide

## Common 500 Internal Server Error Causes

### 1. Query Syntax Issues

**Problem:** The original error likely came from incorrect URL encoding in date ranges.

**WRONG:**
```python
query = 'date_received:[20230101+TO+20231231]'  # Using + signs
```

**CORRECT:**
```python
query = 'date_received:[20240101 TO 20241231]'  # Use spaces, not + signs
```

The Python `requests` library will handle URL encoding automatically. Don't manually encode with `+` signs.

### 2. Field Name Errors

**Common mistakes:**
```python
# WRONG
'generic_name:pacemaker'  # Missing device. prefix
'device_name:pacemaker'   # Wrong field name

# CORRECT
'device.generic_name:pacemaker'
```

### 3. Date Range Formatting

**CORRECT formats:**
```python
# Spaces in the range (let requests encode it)
'date_received:[20240101 TO 20241231]'

# Exact date
'date_received:20240101'

# Last 30 days from now
'date_received:[20250115 TO 20250215]'
```

### 4. Quote Usage

**For single words** - quotes are optional:
```python
'device.generic_name:pacemaker'
```

**For phrases** - quotes are REQUIRED:
```python
'device.generic_name:"insulin infusion pump"'
```

### 5. Boolean Operators

Must be **UPPERCASE**:
```python
# CORRECT
'event_type:Death AND device.generic_name:pacemaker'

# WRONG
'event_type:Death and device.generic_name:pacemaker'
```

## Testing Your Queries

### Step 1: Test in Browser First

Try your query in a browser to see if it works:
```
https://api.fda.gov/device/event.json?search=device.generic_name:pacemaker&limit=1
```

If this works in browser but not in Python, it's a syntax/encoding issue.

### Step 2: Check the Actual URL

The improved script prints the actual URL being called:
```python
print(f"URL: {response.url}")
```

Copy this URL and test it in your browser to see the exact error message.

### Step 3: Start Simple

Begin with the simplest possible query:
```python
# Simplest query - just a device name
results = fetcher.search('device.generic_name:pacemaker', limit=1)
```

Then gradually add complexity:
```python
# Add date range
results = fetcher.search('device.generic_name:pacemaker AND date_received:[20240101 TO 20241231]', limit=10)
```

## Working Query Examples

```python
# Search by device generic name
'device.generic_name:pacemaker'

# Search by brand name
'device.brand_name:medtronic'

# Search by manufacturer
'device.manufacturer_d_name:boston'

# Search by event type
'event_type:Death'

# Search by date range
'date_received:[20240101 TO 20241231]'

# Combined search
'event_type:Injury AND device.generic_name:pacemaker'

# Search with phrase
'device.generic_name:"infusion pump"'

# Multiple conditions
'event_type:Death AND date_received:[20240101 TO 20241231] AND device.manufacturer_d_name:medtronic'
```

## Field Reference

Common searchable fields:
- `device.generic_name` - Generic device type
- `device.brand_name` - Brand name
- `device.manufacturer_d_name` - Manufacturer
- `device.device_name` - Device name
- `event_type` - Death, Injury, Malfunction, Other, No Answer Provided
- `date_received` - YYYYMMDD format
- `date_of_event` - YYYYMMDD format
- `report_number` - Report ID
- `report_source_code` - Source of report

## Rate Limiting

If you're making many requests:

**Without API key:**
- 240 requests per minute
- 120,000 requests per day

**With API key (free):**
- 1,000 requests per minute
- 120,000 requests per day

Get a key at: https://open.fda.gov/apis/authentication/

## Alternative: Direct Download

If the API continues to have issues, you can download bulk data:

```python
import pandas as pd

# Download from FDA website
url = "https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfmaude/textsearch.cfm"

# Then manually download the bulk files and process them
# Files are available at: https://www.fda.gov/medical-devices/medical-device-reporting-mdr-how-report-medical-device-problems/manufacturer-and-user-facility-device-experience-maude
```

## API Status Check

Check if the API is currently operational:
```
https://open.fda.gov/apis/status/
```

## Getting Help

If problems persist:
1. Check FDA's API status page
2. Try your query in the web interface: https://open.fda.gov/apis/device/event/
3. Join the openFDA Google Group for help
4. Check for service announcements at: https://open.fda.gov/updates/

## Quick Fix for Your Error

Replace this line in your code:
```python
# FROM:
query = 'date_received:[20230101+TO+20231231]'

# TO:
query = 'date_received:[20230101 TO 20231231]'  # Space instead of +
```

And make sure you're using the v2 script which has better error handling!
