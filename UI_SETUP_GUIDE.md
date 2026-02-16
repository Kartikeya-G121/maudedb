# MAUDE Database Web UI - Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your FDA API key (optional but recommended for higher rate limits):

```
FDA_API_KEY=your_api_key_here
```

Get a free API key at: https://open.fda.gov/apis/authentication/

### 3. Run the Web Interface

```bash
python maude_ui.py
```

The app will start at: **http://localhost:8050**

## Features

### 🔍 Search Interface
- **Sample Queries**: Pre-built queries for common searches
- **Custom Queries**: Write your own openFDA API queries
- **Max Results**: Control how many reports to fetch (1-5000)

### 📊 Data Display
- **Statistics Dashboard**: Quick overview of total reports, event types, devices, and manufacturers
- **Interactive Table**: 
  - Sort by any column
  - Filter rows in real-time
  - Pagination (25 rows per page by default)
  - Export to CSV

### 💾 Export Options
- Export button to download current results
- Built-in table export feature
- Automatic timestamped filenames

## Sample Queries

The UI includes these pre-built queries:

1. **Pacemaker Reports**: `device.generic_name:"pacemaker"`
2. **Insulin Pump Reports**: `device.generic_name:"insulin+pump"`
3. **Defibrillator Reports**: `device.generic_name:"defibrillator"`
4. **Medtronic Devices**: `device.manufacturer_d_name:"medtronic"`
5. **Death Events**: `event_type:"Death"`
6. **Injury Events**: `event_type:"Injury"`
7. **Recent Reports**: `date_received:[20240101+TO+20240131]`

## Custom Query Examples

Try these in the "Custom Query" field:

```
# Search by multiple conditions
device.generic_name:"insulin+pump"+AND+event_type:"Injury"

# Search by manufacturer and date
device.manufacturer_d_name:"abbott"+AND+date_received:[20240101+TO+20240331]

# Search by device class
device.openfda.device_class:"3"+AND+event_type:"Death"

# Search for specific brand
device.brand_name:"freestyle"+AND+date_received:[20230101+TO+20231231]
```

## Configuration Options

Edit `.env` to customize:

```bash
# API Configuration
FDA_API_KEY=                # Your FDA API key (optional)
DEFAULT_LIMIT=100           # Default number of results per API call
DEFAULT_MAX_RESULTS=1000    # Default max results for searches

# UI Settings
UI_HOST=localhost           # Server host (use 0.0.0.0 for network access)
UI_PORT=8050               # Server port
ROWS_PER_PAGE=50           # Rows per page in the table
```

## Screenshots

### Main Interface
- Search panel on the left
- Results and statistics on the right
- Interactive data table at the bottom

### Data Table Features
- Click column headers to sort
- Type in filter boxes below headers to filter
- Use pagination controls to navigate
- Click "Export" button in table to download

## Tips for Best Results

1. **Start with Sample Queries**: Get familiar with the data structure
2. **Be Specific**: Combine device/manufacturer with date ranges
3. **Start Small**: Begin with 100-500 results, then increase
4. **Use Filters**: Filter the table after loading to explore data
5. **Export Often**: Download interesting result sets for offline analysis

## Troubleshooting

### "No results found"
- Check your query syntax
- Try a sample query first
- Verify the date range is valid (YYYYMMDD format)

### "500 Server Error"
- Your query is too broad
- Add device or manufacturer filters
- Use shorter date ranges
- See TROUBLESHOOTING.md for details

### Table is slow
- Reduce max results
- Use table filters to narrow down
- Export and analyze in Excel/Python for large datasets

### Port already in use
- Change `UI_PORT` in `.env`
- Or kill the process using port 8050:
  ```bash
  lsof -ti:8050 | xargs kill -9
  ```

## Advanced Usage

### Run on Network (Access from Other Devices)

Edit `.env`:
```bash
UI_HOST=0.0.0.0
UI_PORT=8050
```

Then access from other devices at: `http://YOUR_IP_ADDRESS:8050`

### Customize Table Display

Edit `maude_ui.py` and modify the `display_columns` list to show different fields:

```python
display_columns = [
    'report_number',
    'date_received',
    'event_type',
    'device_generic_name',
    'device_brand_name',
    'device_manufacturer',
    'outcome',
    'event_description',  # Add description
]
```

### Change Theme

The UI uses Bootstrap. Change the theme by modifying:

```python
external_stylesheets=[dbc.themes.BOOTSTRAP]  # Try DARKLY, FLATLY, etc.
```

Available themes: https://bootswatch.com/

## Command Line Alternative

If you prefer the command line, use `maude_api_fetch.py`:

```python
from maude_api_fetch import MAUDEFetcher

fetcher = MAUDEFetcher()
results = fetcher.fetch_all('device.generic_name:"pacemaker"', max_results=500)
df = fetcher.parse_to_dataframe(results)
fetcher.save_to_csv(df, 'pacemaker_reports.csv')
```

## Resources

- **FDA OpenFDA API**: https://open.fda.gov/apis/device/event/
- **Query Syntax**: https://open.fda.gov/apis/query-syntax/
- **API Authentication**: https://open.fda.gov/apis/authentication/
- **MAUDE Database Info**: https://www.fda.gov/medical-devices/mandatory-reporting-requirements-manufacturers-importers-and-device-user-facilities/manufacturer-and-user-facility-device-experience-maude

## Support

For issues or questions:
1. Check TROUBLESHOOTING.md
2. Review the README.md
3. Test with `test_maude_api.py`
4. Visit FDA's openFDA documentation

---

**Note**: This tool is for research and informational purposes. Always verify critical information with official FDA sources.
