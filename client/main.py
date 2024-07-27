import requests
import time
import json

# function to query the local screen-pipe operation.

sp_url = "http://localhost:3030"
backend_url = "http://localhost:8000"


def get_screenpipe_activity():
    """Get latest OCR info from screenpipe"""
    print("getting screenpipe data")
    while True:
        try:
            response = requests.get(
                f"{sp_url}/search?limit=1&offset=0&content_type=ocr", timeout=(15, 30)
            )
            response.raise_for_status()
            print("screenpipe data fetched")
            return response.json()
        except requests.exceptions.Timeout:
            print("Request timed out. Retrying...")
            continue
        except requests.exceptions.RequestException as e:
            print(f"Error fetching screenpipe activity: {e}")
            return None
    # ocr_content_str: str = recent_ocr["data"][0]["content"]["text"]

    # print(ocr_content_str)

    # if query bounces, assume user isn't on computer

    # run OCR through


def main():
    """Run query on an interval"""

    interval = 180  # seconds

    while True:
        res = get_screenpipe_activity()
        # send OCR info to server
        print(f"posting request with OCR data: {res}")
        try:
            requests.post(f"{backend_url}/handle_activity", json=res)
            print("request posted")
        except requests.exceptions.Timeout:
            print("Request timed out. Retrying...")
            continue

        print(f"snoozing for {interval} seconds")
        time.sleep(interval)

    return None


main()
