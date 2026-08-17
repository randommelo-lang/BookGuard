import os
import time

import httpx
from dotenv import load_dotenv


load_dotenv()

BRIGHTDATA_API_KEY = os.getenv("BRIGHTDATA_API_KEY")
BRIGHT_DATA_COLLECTOR_ID = os.getenv("BRIGHT_DATA_COLLECTOR_ID")


def trigger_collector(book_url: str):
    endpoint = (
        "https://api.brightdata.com/dca/trigger"
        f"?collector={BRIGHT_DATA_COLLECTOR_ID}&queue_next=1"
    )

    headers = {
        "Authorization": f"Bearer {BRIGHTDATA_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = [
        {
            "url": book_url
        }
    ]

    response = httpx.post(
        endpoint,
        headers=headers,
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    return response.json()


def get_collection(collection_id: str):
    url = "https://api.brightdata.com/dca/dataset"

    headers = {
        "Authorization": f"Bearer {BRIGHTDATA_API_KEY}",
    }

    params = {
        "id": collection_id,
    }

    response = httpx.get(
        url,
        headers=headers,
        params=params,
        timeout=60,
    )

    response.raise_for_status()

    return response.json()


def wait_for_collection(collection_id: str):
    while True:
        result = get_collection(collection_id)

        status = result.get("status")

        if status:
            print(f"Collection status: {status}")

        if status in {"collecting", "building"}:
            time.sleep(30)
            continue

        return result


def scrape_book(book_url: str):
    if not BRIGHTDATA_API_KEY:
        raise RuntimeError("BRIGHTDATA_API_KEY is not configured")

    if not BRIGHT_DATA_COLLECTOR_ID:
        raise RuntimeError("BRIGHT_DATA_COLLECTOR_ID is not configured")

    result = trigger_collector(book_url)

    collection_id = result["collection_id"]

    return wait_for_collection(collection_id)