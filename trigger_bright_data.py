#!/usr/bin/env python3
"""
Bright Data Web Scraper IDE Collector Trigger Script
Automates triggering of the Bright Data collector via REST API.
"""

import requests
import json
import sys


def trigger_bright_data_collector(keyword="laptop"):
    """
    Trigger Bright Data collector for Amazon search scraping.
    
    Args:
        keyword (str): The search keyword for Amazon. Defaults to "laptop".
    
    Returns:
        dict: Response data containing response_id if successful, None otherwise.
    """
    # Bright Data API endpoint
    url = "https://api.brightdata.com/dca/trigger?collector=c_mklpmnlj27vssrojsh&queue_next=1"
    
    # Authentication header
    headers = {
        "Authorization": "Bearer c32ca331-b5a1-4124-b71b-d59fb3b7ecf5",
        "Content-Type": "application/json"
    }
    
    # Payload with keyword
    payload = {
        "keyword": keyword
    }
    
    try:
        print("Initiating Bright Data Managed Scraper...")
        print(f"Search Keyword: {keyword}")
        print("-" * 50)
        
        # Send POST request
        response = requests.post(url, headers=headers, json=payload)
        
        # Check if request was successful
        if response.status_code == 200:
            response_data = response.json()
            
            # Extract and display response_id
            response_id = response_data.get("response_id") or response_data.get("id") or response_data.get("job_id")
            
            print("Success: Collector Triggered!")
            print("-" * 50)
            print(f"Response ID: {response_id}")
            print(f"Status Code: {response.status_code}")
            
            # Print full response for debugging (optional)
            print("\nFull Response:")
            print(json.dumps(response_data, indent=2))
            
            return response_data
        else:
            print(f"Error: Request failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to connect to Bright Data API")
        print(f"Details: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: An unexpected error occurred")
        print(f"Details: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # Allow keyword to be passed as command-line argument
    keyword = sys.argv[1] if len(sys.argv) > 1 else "laptop"
    
    trigger_bright_data_collector(keyword)
