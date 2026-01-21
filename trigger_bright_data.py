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
        str: Response ID if successful, None otherwise.
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
        print("Step 1: Authenticating with Bright Data Cloud...")
        print(f"Search Keyword: {keyword}")
        print("-" * 60)
        
        # Send POST request
        print("Step 2: Sending trigger request to Bright Data API...")
        response = requests.post(url, headers=headers, json=payload)
        
        # Check if request was successful
        if response.status_code == 200:
            response_data = response.json()
            
            # Extract response_id
            response_id = response_data.get("response_id") or response_data.get("id") or response_data.get("job_id")
            
            if not response_id:
                print("Error: No response_id found in API response")
                print(f"Response: {json.dumps(response_data, indent=2)}")
                return None
            
            print("Step 3: Collector triggered successfully!")
            print("-" * 60)
            print(f"Response ID: {response_id}")
            print(f"Status Code: {response.status_code}")
            
            # Save response_id to file
            try:
                print("Step 4: Saving job ID to current_job.txt...")
                with open("current_job.txt", "w", encoding="utf-8") as f:
                    f.write(response_id)
                print("✓ Job ID saved successfully")
                print("-" * 60)
            except IOError as e:
                print(f"Warning: Failed to save job ID to file: {str(e)}")
            
            return response_id
        else:
            print(f"Error: Request failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print("Error: Failed to connect to Bright Data API")
        print(f"Details: {str(e)}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print("Error: Failed to parse API response as JSON")
        print(f"Details: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print("Error: An unexpected error occurred")
        print(f"Details: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    keyword = sys.argv[1] if len(sys.argv) > 1 else "laptop"
    response_id = trigger_bright_data_collector(keyword)
    
    if response_id:
        print(f"\n✓ Success! Job ID: {response_id}")
        print("Next step: Run 'python poll_results.py' to retrieve results")
    else:
        print("\n✗ Failed to trigger collector. Please check the logs above.")
        sys.exit(1)
