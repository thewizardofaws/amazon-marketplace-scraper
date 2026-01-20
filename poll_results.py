#!/usr/bin/env python3
"""
Bright Data Scraper Results Poller
Polls for job completion and downloads results once ready.
"""

import requests
import json
import sys
import time
from datetime import datetime, timedelta


def poll_bright_data_results(response_id, api_key, timeout_minutes=30, poll_interval=10):
    """
    Poll Bright Data API for job results until ready or timeout.
    
    Args:
        response_id (str): The response_id from the initial trigger request.
        api_key (str): Bright Data API Bearer token.
        timeout_minutes (int): Maximum time to wait for results in minutes. Default: 30.
        poll_interval (int): Seconds to wait between poll attempts. Default: 10.
    
    Returns:
        dict: The response data if successful, None otherwise.
    """
    url = f"https://api.brightdata.com/dca/get_result?response_id={response_id}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    timeout_seconds = timeout_minutes * 60
    start_time = datetime.now()
    end_time = start_time + timedelta(seconds=timeout_seconds)
    attempt = 0
    
    print("Polling Bright Data for job results...")
    print(f"Response ID: {response_id}")
    print(f"Timeout: {timeout_minutes} minutes")
    print(f"Poll Interval: {poll_interval} seconds")
    print("-" * 50)
    
    while datetime.now() < end_time:
        attempt += 1
        elapsed = (datetime.now() - start_time).total_seconds()
        
        try:
            print(f"[Attempt {attempt}] Checking status... (Elapsed: {elapsed:.0f}s)")
            
            response = requests.get(url, headers=headers)
            
            # Check if request was successful
            if response.status_code != 200:
                print(f"Warning: Received status code {response.status_code}")
                print(f"Response: {response.text}")
                time.sleep(poll_interval)
                continue
            
            # Check if response is empty
            if not response.text or response.text.strip() == "":
                print("Job still running (empty response)...")
                time.sleep(poll_interval)
                continue
            
            # Try to parse JSON response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                # If not JSON, check if it's a text response indicating "running"
                response_text = response.text.strip().lower()
                if "running" in response_text or response_text == "":
                    print("Job still running...")
                    time.sleep(poll_interval)
                    continue
                else:
                    print(f"Unexpected response format: {response.text[:100]}")
                    time.sleep(poll_interval)
                    continue
            
            # Check if response indicates job is still running
            # This could be in various formats, so check common patterns
            if isinstance(response_data, dict):
                status = response_data.get("status", "").lower()
                if status in ["running", "pending", "processing"]:
                    print(f"Job status: {status.capitalize()}...")
                    time.sleep(poll_interval)
                    continue
            
            # Check for empty results
            if isinstance(response_data, dict) and not response_data:
                print("Job still running (empty JSON object)...")
                time.sleep(poll_interval)
                continue
            
            # If we get here, we have data!
            print("\n" + "=" * 50)
            print("Success: Job completed! Data received.")
            print("=" * 50)
            return response_data
            
        except requests.exceptions.RequestException as e:
            print(f"Network error: {str(e)}")
            print("Retrying...")
            time.sleep(poll_interval)
            continue
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            time.sleep(poll_interval)
            continue
    
    # Timeout reached
    print("\n" + "=" * 50)
    print(f"Timeout: Job did not complete within {timeout_minutes} minutes")
    print("=" * 50)
    return None


def save_results(data, filename="amazon_results.json"):
    """
    Save results to a JSON file and print summary.
    
    Args:
        data: The data to save (dict, list, etc.)
        filename (str): Output filename. Default: "amazon_results.json"
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Count items
        count = 0
        if isinstance(data, list):
            count = len(data)
        elif isinstance(data, dict):
            # Try to find items in common structures
            if "items" in data:
                count = len(data["items"]) if isinstance(data["items"], list) else 0
            elif "results" in data:
                count = len(data["results"]) if isinstance(data["results"], list) else 0
            elif "data" in data:
                if isinstance(data["data"], list):
                    count = len(data["data"])
                elif isinstance(data["data"], dict):
                    count = 1  # Single object
            else:
                # Count top-level keys or assume it's a single item
                count = len(data) if data else 0
        
        print(f"\nData Downloaded Successfully!")
        print(f"Saved to: {filename}")
        print(f"Total items: {count}")
        print(f"File size: {len(json.dumps(data).encode('utf-8'))} bytes")
        
    except Exception as e:
        print(f"Error saving results to file: {str(e)}")
        raise


def main():
    """Main execution function."""
    # Parse command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python poll_results.py <response_id> [timeout_minutes] [poll_interval]")
        print("\nExample:")
        print('  python poll_results.py "abc123xyz"')
        print('  python poll_results.py "abc123xyz" 45 15')
        sys.exit(1)
    
    response_id = sys.argv[1]
    timeout_minutes = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    poll_interval = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    
    # API key from requirements
    api_key = "c32ca331-b5a1-4124-b71b-d59fb3b7ecf5"
    
    # Poll for results
    results = poll_bright_data_results(response_id, api_key, timeout_minutes, poll_interval)
    
    if results is None:
        print("\nFailed to retrieve results. Please check:")
        print("1. The response_id is correct")
        print("2. The job is still running (may need more time)")
        print("3. The API key has proper permissions")
        sys.exit(1)
    
    # Save results
    save_results(results, "amazon_results.json")


if __name__ == "__main__":
    main()
