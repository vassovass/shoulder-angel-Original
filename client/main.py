import requests
import time
import json

# function to query the local screen-pipe operation.


def get_screenpipe_activity():
    """Get latest OCR info from screenpipe"""
    # query most recent OCR from screenpipe
    sp_url = "https://localhost:3030"
    backend_url = "https://localhost:8000"

    res = requests.get(f"{sp_url}/search?limit=1&offset=0&content_type=ocr")

    try:
        res_json = json.loads(res)
    except Exception as e:
        print(e)

    ocr_content_str: str = recent_ocr["data"][0]["content"]["text"]

    print(ocr_content_str)

    # if query bounces, assume user isn't on computer

    # run OCR through
    return ocr_json


def main():
    """Run query on an interval"""

    interval = 60  # seconds

    while True:
        res = get_screenpipe_activity()
        # send OCR info to server
        requests.post(f"{backend_url}/handle_activity", json=res)

        time.sleep(interval)

    return None
