#!/usr/bin/env python3
"""
MAUDE Database API Fetcher
Fetch and parse medical device adverse event data from FDA's openFDA API
"""

import requests
import json
import pandas as pd
from datetime import datetime
import time

class MAUDEFetcher:
    """Class to fetch and parse MAUDE data from openFDA API"""
    
    BASE_URL = "https://api.fda.gov/device/event.json"
    
    def __init__(self, api_key=None):
        """
        Initialize the fetcher
        
        Args:
            api_key (str, optional): FDA API key for higher rate limits
        """
        self.api_key = api_key
        self.session = requests.Session()
    
    def search(self, search_query, limit=100, skip=0):
        """
        Search MAUDE database
        
        Args:
            search_query (str): Search query (e.g., 'device.generic_name:"pacemaker"')
            limit (int): Number of results to return (max 1000)
            skip (int): Number of results to skip (for pagination)
            
        Returns:
            dict: API response with results
        """
        # Build URL manually to avoid over-encoding
        # FDA API is sensitive to how brackets and + signs are encoded
        url = f"{self.BASE_URL}?search={search_query}&limit={min(limit, 1000)}&skip={skip}"
        
        if self.api_key:
            url += f"&api_key={self.api_key}"
        
        print(f"Query: {search_query}")
        print(f"URL: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 500:
                print(f"HTTP Error 500: {e}")
                print(f"Response: {response.text}")
                print(f"Server error (500). Try:")
                print("  1. Narrowing your date range")
                print("  2. Adding a device type to your query")
                print(f"  3. Your query was: {search_query}")
            elif response.status_code == 404:
                print(f"No results found for query: {search_query}")
            else:
                print(f"HTTP Error {response.status_code}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return None
    
    def fetch_all(self, search_query, max_results=None, delay=0.5):
        """
        Fetch all results for a query (handles pagination automatically)
        
        Args:
            search_query (str): Search query
            max_results (int, optional): Maximum number of results to fetch
            delay (float): Delay between requests in seconds (to respect rate limits)
            
        Returns:
            list: All results
        """
        all_results = []
        skip = 0
        limit = 1000  # Maximum per request
        
        print(f"Fetching data for query: {search_query}")
        
        while True:
            print(f"Fetching results {skip} to {skip + limit}...")
            
            data = self.search(search_query, limit=limit, skip=skip)
            
            if not data or 'results' not in data:
                break
            
            results = data['results']
            all_results.extend(results)
            
            # Check if we've reached the end or max_results
            total_available = data['meta']['results']['total']
            print(f"Retrieved {len(all_results)} of {total_available} total results")
            
            if len(results) < limit or (max_results and len(all_results) >= max_results):
                break
            
            skip += limit
            
            if max_results and skip >= max_results:
                break
            
            # Rate limiting - be nice to the API
            time.sleep(delay)
        
        print(f"Total results fetched: {len(all_results)}")
        return all_results[:max_results] if max_results else all_results
    
    def parse_to_dataframe(self, results):
        """
        Parse results into a pandas DataFrame
        
        Args:
            results (list): List of result objects from API
            
        Returns:
            pd.DataFrame: Parsed data
        """
        parsed_data = []
        
        for result in results:
            # Extract basic report info
            row = {
                'report_number': result.get('report_number'),
                'event_type': result.get('event_type'),
                'date_received': result.get('date_received'),
                'date_of_event': result.get('date_of_event'),
                'report_source_code': result.get('report_source_code'),
                'manufacturer_contact_country': result.get('manufacturer_contact_t_country')
            }
            
            # Extract device information (first device if multiple)
            if 'device' in result and len(result['device']) > 0:
                device = result['device'][0]
                row['device_brand_name'] = device.get('brand_name')
                row['device_generic_name'] = device.get('generic_name')
                row['device_manufacturer'] = device.get('manufacturer_d_name')
                row['device_class'] = device.get('openfda', {}).get('device_class')
                row['device_name'] = device.get('device_name')
            
            # Extract patient information
            if 'patient' in result and len(result['patient']) > 0:
                patient = result['patient'][0]
                row['patient_sequence_number'] = patient.get('patient_sequence_number')
                
                # Extract patient problems if available
                if 'sequence_number_outcome' in patient:
                    outcomes = patient['sequence_number_outcome']
                    if outcomes:
                        row['outcome'] = outcomes[0] if isinstance(outcomes, list) else outcomes
            
            # Extract event description (narrative text)
            if 'mdr_text' in result:
                texts = result['mdr_text']
                descriptions = [t.get('text', '') for t in texts if t.get('text_type_code') in ['Description of Event', 'Additional Manufacturer Narrative']]
                row['event_description'] = ' | '.join(descriptions) if descriptions else ''
            
            parsed_data.append(row)
        
        return pd.DataFrame(parsed_data)
    
    def save_to_csv(self, df, filename):
        """Save DataFrame to CSV file"""
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
    
    def save_to_json(self, results, filename):
        """Save raw results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Data saved to {filename}")


# Example usage functions
def example_1_simple_search():
    """Example 1: Simple search for pacemaker reports"""
    print("\n=== Example 1: Simple Pacemaker Search ===")
    
    fetcher = MAUDEFetcher()
    
    # Search for pacemaker-related adverse events
    results = fetcher.search('device.generic_name:"pacemaker"', limit=10)
    
    if results and 'results' in results:
        print(f"Total matching reports: {results['meta']['results']['total']}")
        print(f"Retrieved: {len(results['results'])} reports")
        
        # Show first report
        if results['results']:
            first_report = results['results'][0]
            print(f"\nFirst report number: {first_report.get('report_number')}")
            print(f"Event type: {first_report.get('event_type')}")


def example_2_date_range_search():
    """Example 2: Search by date range"""
    print("\n=== Example 2: Date Range Search ===")
    
    fetcher = MAUDEFetcher()
    
    # Search for reports received in a specific month (narrower range to avoid 500 errors)
    # Using a device type + date range works better than date alone
    query = 'device.generic_name:"pacemaker"+AND+date_received:[20240101+TO+20240131]'
    results = fetcher.search(query, limit=100)
    
    if results and 'results' in results:
        print(f"Pacemaker reports in Jan 2024: {results['meta']['results']['total']}")
        
        # Parse to DataFrame
        df = fetcher.parse_to_dataframe(results['results'])
        print(f"\nDataFrame shape: {df.shape}")
        print("\nFirst few rows:")
        print(df[['report_number', 'date_received', 'event_type', 'device_brand_name']].head())


def example_3_manufacturer_search():
    """Example 3: Search by manufacturer"""
    print("\n=== Example 3: Manufacturer Search ===")
    
    fetcher = MAUDEFetcher()
    
    # Search for a specific manufacturer (example: Medtronic)
    query = 'device.manufacturer_d_name:"medtronic"'
    results = fetcher.search(query, limit=50)
    
    if results and 'results' in results:
        df = fetcher.parse_to_dataframe(results['results'])
        
        print(f"\nTotal reports: {len(df)}")
        print(f"\nDevices by type:")
        print(df['device_generic_name'].value_counts().head(10))


def example_4_fetch_and_save():
    """Example 4: Fetch multiple pages and save to CSV"""
    print("\n=== Example 4: Fetch Multiple Pages and Save ===")
    
    fetcher = MAUDEFetcher()
    
    # Fetch up to 500 insulin pump reports
    query = 'device.generic_name:"insulin+pump"'
    results = fetcher.fetch_all(query, max_results=500, delay=0.5)
    
    if results:
        # Convert to DataFrame
        df = fetcher.parse_to_dataframe(results)
        
        # Save to CSV
        fetcher.save_to_csv(df, 'insulin_pump_reports.csv')
        
        # Basic statistics
        print(f"\nEvent types distribution:")
        print(df['event_type'].value_counts())


def example_5_complex_query():
    """Example 5: Complex query with multiple conditions"""
    print("\n=== Example 5: Complex Query ===")
    
    fetcher = MAUDEFetcher()
    
    # Search for serious injuries with specific device in 2023
    query = 'event_type:"Injury"+AND+date_received:[20230101+TO+20231231]+AND+device.generic_name:"defibrillator"'
    results = fetcher.search(query, limit=100)
    
    if results and 'results' in results:
        df = fetcher.parse_to_dataframe(results['results'])
        
        print(f"\nTotal matching reports: {results['meta']['results']['total']}")
        print(f"\nManufacturers involved:")
        print(df['device_manufacturer'].value_counts().head())


def example_6_export_json():
    """Example 6: Export raw JSON data"""
    print("\n=== Example 6: Export Raw JSON ===")
    
    fetcher = MAUDEFetcher()
    
    query = 'device.generic_name:"stent"'
    results = fetcher.fetch_all(query, max_results=100)
    
    if results:
        fetcher.save_to_json(results, 'stent_reports.json')
        print("Raw JSON data saved")


def example_7_working_queries():
    """Example 7: Collection of queries that work reliably"""
    print("\n=== Example 7: Reliable Query Patterns ===")
    
    fetcher = MAUDEFetcher()
    
    # These query patterns work well and avoid 500 errors:
    
    queries = [
        ('Device by name', 'device.generic_name:"pacemaker"'),
        ('Recent reports', 'date_received:[20240101+TO+20240131]'),
        ('Manufacturer', 'device.manufacturer_d_name:"medtronic"'),
        ('Death events', 'event_type:"Death"'),
        ('Brand name', 'device.brand_name:"freestyle"'),
    ]
    
    for name, query in queries:
        print(f"\n{name}: {query}")
        results = fetcher.search(query, limit=5)
        if results and 'results' in results:
            print(f"  ✓ Found {results['meta']['results']['total']} reports")
        else:
            print(f"  ✗ Query failed")
        time.sleep(0.5)  # Be nice to the API


if __name__ == "__main__":
    print("MAUDE Database API Fetcher Examples")
    print("=" * 50)
    
    # Run examples (uncomment the ones you want to try)
    
    example_1_simple_search()
    # example_2_date_range_search()
    # example_3_manufacturer_search()
    # example_4_fetch_and_save()
    # example_5_complex_query()
    # example_6_export_json()
    # example_7_working_queries()  # NEW: Test multiple query patterns
    
    print("\n" + "=" * 50)
    print("Examples complete!")
    print("\nTo use this script:")
    print("1. Uncomment the examples you want to run")
    print("2. Modify search queries for your specific needs")
    print("3. Optional: Get an API key from https://open.fda.gov/apis/authentication/")
    print("\nTIP: If you get 500 errors, try:")
    print("  - Adding a device type to date range queries")
    print("  - Using shorter date ranges (month instead of year)")
    print("  - Starting with specific device/manufacturer searches")