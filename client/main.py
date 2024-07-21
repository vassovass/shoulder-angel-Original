import requests
import time
import json

# function to query the local screen-pipe operation.

sp_url = "http://localhost:3030"
backend_url = "http://localhost:8000"


def get_screenpipe_activity():
    """Get latest OCR info from screenpipe"""
    # query most recent OCR from screenpipe

    res = requests.get(f"{sp_url}/search?limit=1&offset=0&content_type=ocr").json()

    try:
        res_json = res
        return res_json
    except Exception as e:
        print(e)
        return None

    # ocr_content_str: str = recent_ocr["data"][0]["content"]["text"]

    # print(ocr_content_str)

    # if query bounces, assume user isn't on computer

    # run OCR through


def main():
    """Run query on an interval"""

    interval = 120  # seconds

    while True:
        res = get_screenpipe_activity()
        # send OCR info to server
        requests.post(f"{backend_url}/handle_activity", json=res)

        time.sleep(interval)

    return None


main()
