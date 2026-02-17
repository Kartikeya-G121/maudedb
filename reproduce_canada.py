
import logging
import traceback
# Adjusted import for running inside maudedb directory
try:
    from canada_fetch import CanadaRecallsFetcher
except ImportError:
    # Fallback if running from parent directory
    from maudedb.canada_fetch import CanadaRecallsFetcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_canada_fetch():
    print("Testing CanadaRecallsFetcher...")
    try:
        fetcher = CanadaRecallsFetcher()
        print("Fetching all raw data...")
        data = fetcher.fetch_all_raw()
        print(f"Successfully fetched {len(data)} records.")
        
        print("Fetching medical devices only...")
        # Note: fetch_medical_devices calls fetch_all_raw internaly
        devices = fetcher.fetch_medical_devices()
        print(f"Found {len(devices)} medical device records.")
        
        if devices:
            print("First record sample:")
            print(devices[0])
            
        print("Testing search...")
        df = fetcher.search() 
        print(f"Search returned DataFrame with shape: {df.shape}")
        print(df.head())
        
    except Exception as e:
        print(f"Error encountered: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_canada_fetch()
