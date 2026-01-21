#!/usr/bin/env python3
"""
Bright Data Scraper Results Poller
Polls for job completion and downloads results once ready.
"""

import requests
import json
import sys
import time
import os
from datetime import datetime, timedelta


def read_job_id(filename="current_job.txt"):
    """
    Read response_id from the current job file.
    
    Args:
        filename (str): Path to the job ID file. Default: "current_job.txt"
    
    Returns:
        str: The response_id if found, None otherwise.
    """
    try:
        if not os.path.exists(filename):
            print(f"Error: Job ID file '{filename}' not found.")
            print("Please run trigger_bright_data.py first to create a job.")
            return None
        
        with open(filename, "r", encoding="utf-8") as f:
            response_id = f.read().strip()
        
        if not response_id:
            print(f"Error: Job ID file '{filename}' is empty.")
            return None
        
        return response_id
    except IOError as e:
        print(f"Error: Failed to read job ID from '{filename}': {str(e)}")
        return None


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
    
    print("Step 1: Authenticating with Bright Data Cloud...")
    print(f"Job ID: {response_id}")
    print(f"Timeout: {timeout_minutes} minutes | Poll Interval: {poll_interval} seconds")
    print("-" * 60)
    
    while datetime.now() < end_time:
        attempt += 1
        elapsed = (datetime.now() - start_time).total_seconds()
        
        try:
            print(f"Step 2: Polling attempt #{attempt}... (Elapsed: {elapsed:.0f}s)")
            
            response = requests.get(url, headers=headers)
            
            # Check if request was successful
            if response.status_code != 200:
                print(f"Warning: Received status code {response.status_code}")
                print(f"Response: {response.text}")
                time.sleep(poll_interval)
                continue
            
            # Check if response is empty
            if not response.text or response.text.strip() == "":
                print("Status: Job still running (empty response)...")
                time.sleep(poll_interval)
                continue
            
            # Try to parse JSON response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                # If not JSON, check if it's a text response indicating "running"
                response_text = response.text.strip().lower()
                if "running" in response_text or response_text == "":
                    print("Status: Job still running...")
                    time.sleep(poll_interval)
                    continue
                else:
                    print(f"Warning: Unexpected response format: {response.text[:100]}")
                    time.sleep(poll_interval)
                    continue
            
            # Check if response indicates job is still running
            if isinstance(response_data, dict):
                status = response_data.get("status", "").lower()
                if status in ["running", "pending", "processing"]:
                    print(f"Status: Job {status.capitalize()}...")
                    time.sleep(poll_interval)
                    continue
            
            # Check for empty results
            if isinstance(response_data, dict) and not response_data:
                print("Status: Job still running (empty JSON object)...")
                time.sleep(poll_interval)
                continue
            
            # If we get here, we have data!
            print("\n" + "=" * 60)
            print("Step 3: Job completed! Data received successfully.")
            print("=" * 60)
            return response_data
            
        except requests.exceptions.RequestException as e:
            print(f"Network error: {str(e)}")
            print("Retrying in next interval...")
            time.sleep(poll_interval)
            continue
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            time.sleep(poll_interval)
            continue
    
    # Timeout reached
    print("\n" + "=" * 60)
    print(f"Timeout: Job did not complete within {timeout_minutes} minutes")
    print("=" * 60)
    return None


def extract_product_titles(data):
    """
    Extract product titles from the response data.
    
    Args:
        data: The response data (dict, list, etc.)
    
    Returns:
        list: List of product titles (first 3)
    """
    titles = []
    
    try:
        # Handle various data structures
        items = None
        
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            # Try common keys
            for key in ["items", "results", "data", "products"]:
                if key in data and isinstance(data[key], list):
                    items = data[key]
                    break
            
            # If no list found, check if dict contains title fields
            if not items and "title" in data:
                return [data.get("title", "N/A")[:100]]
        
        if items:
            for item in items[:3]:
                if isinstance(item, dict):
                    # Try common title field names
                    for title_key in ["title", "product_title", "name", "product_name"]:
                        if title_key in item:
                            titles.append(str(item[title_key])[:100])
                            break
        
        return titles[:3] if titles else []
    except (AttributeError, KeyError, TypeError) as e:
        print(f"Warning: Could not extract product titles: {str(e)}")
        return []


def save_results(data, filename="amazon_results.json"):
    """
    Save results to a JSON file and print summary.
    
    Args:
        data: The data to save (dict, list, etc.)
        filename (str): Output filename. Default: "amazon_results.json"
    
    Returns:
        int: Number of items saved
    """
    try:
        print(f"Step 4: Saving results to {filename}...")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Count items
        count = 0
        if isinstance(data, list):
            count = len(data)
        elif isinstance(data, dict):
            # Try to find items in common structures
            for key in ["items", "results", "data", "products"]:
                if key in data and isinstance(data[key], list):
                    count = len(data[key])
                    break
            if count == 0:
                count = len(data) if data else 0
        
        print(f"✓ Results saved successfully")
        print(f"  File: {filename}")
        print(f"  Total items: {count}")
        print(f"  File size: {len(json.dumps(data).encode('utf-8'))} bytes")
        print("-" * 60)
        
        return count
        
    except IOError as e:
        print(f"Error: Failed to save results to file: {str(e)}")
        raise


def main():
    """Main execution function."""
    # API key
    api_key = "c32ca331-b5a1-4124-b71b-d59fb3b7ecf5"
    
    # Read response_id from file
    response_id = read_job_id("current_job.txt")
    if not response_id:
        sys.exit(1)
    
    # Parse optional command-line arguments
    timeout_minutes = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    poll_interval = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    # Poll for results
    results = poll_bright_data_results(response_id, api_key, timeout_minutes, poll_interval)
    
    if results is None:
        print("\n✗ Failed to retrieve results. Please check:")
        print("  1. The job ID is correct")
        print("  2. The job is still running (may need more time)")
        print("  3. The API key has proper permissions")
        sys.exit(1)
    
    # Save results
    item_count = save_results(results, "amazon_results.json")
    
    # Extract and print first 3 product titles
    print("Step 5: Verifying data quality...")
    titles = extract_product_titles(results)
    
    if titles:
        print(f"\n✓ Sample Product Titles (first {min(3, len(titles))}):")
        print("-" * 60)
        for i, title in enumerate(titles, 1):
            print(f"  {i}. {title}")
    else:
        print("\n⚠ Could not extract product titles from response.")
        print("   Data structure may differ from expected format.")
    
    print("-" * 60)
    print(f"\n✓ Complete! Scraped {item_count} items from Amazon.")


if __name__ == "__main__":
    main()
