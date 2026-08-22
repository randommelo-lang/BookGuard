import os
import time

import httpx
from dotenv import load_dotenv


load_dotenv()

BRIGHTDATA_API_KEY = os.getenv("BRIGHTDATA_API_KEY")
BRIGHT_DATA_COLLECTOR_ID = os.getenv("BRIGHT_DATA_COLLECTOR_ID")
BRIGHT_DATA_SEARCH_COLLECTOR_ID = os.getenv(
    "BRIGHT_DATA_SEARCH_COLLECTOR_ID"
)
BRIGHT_DATA_AMAZON_COLLECTOR_ID = os.getenv(
    "BRIGHT_DATA_AMAZON_COLLECTOR_ID"
)
BRIGHT_DATA_AMAZON_PRODUCT_COLLECTOR_ID = os.getenv(
    "BRIGHT_DATA_AMAZON_PRODUCT_COLLECTOR_ID"
)
BRIGHT_DATA_FLIPKART_DATASET_ID = os.getenv(
    "BRIGHT_DATA_FLIPKART_DATASET_ID"
)


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

    text = response.text.strip()

    if not text:
        return {}

    # Normal JSON response
    try:
        return response.json()
    except ValueError:
        pass

    # Bright Data can return multiple JSON objects,
    # one per line, when a collection contains multiple results.
    records = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        try:
            records.append(httpx.Response(
                200,
                content=line,
            ).json())
        except ValueError:
            continue

    if records:
        return records

    raise ValueError(
        "Bright Data returned an invalid JSON response"
    )


def wait_for_collection(collection_id: str):
    while True:
        result = get_collection(collection_id)

        # Completed collection containing multiple records
        if isinstance(result, list):
            print(f"Collection returned {len(result)} records")
            return result

        status = result.get("status")

        if status:
            print(f"Collection status: {status}")

        if status in {"collecting", "building"}:
            time.sleep(30)
            continue

        return result


def scrape_book(book_url: str):
    if not BRIGHTDATA_API_KEY:
        raise RuntimeError(
            "BRIGHTDATA_API_KEY is not configured"
        )

    if not BRIGHT_DATA_COLLECTOR_ID:
        raise RuntimeError(
            "BRIGHT_DATA_COLLECTOR_ID is not configured"
        )

    result = trigger_collector(book_url)

    collection_id = result["collection_id"]

    return wait_for_collection(collection_id)


def trigger_search_collector(search_url: str):
    if not BRIGHTDATA_API_KEY:
        raise RuntimeError(
            "BRIGHTDATA_API_KEY is not configured"
        )

    if not BRIGHT_DATA_SEARCH_COLLECTOR_ID:
        raise RuntimeError(
            "BRIGHT_DATA_SEARCH_COLLECTOR_ID is not configured"
        )

    endpoint = (
        "https://api.brightdata.com/dca/trigger"
        f"?collector={BRIGHT_DATA_SEARCH_COLLECTOR_ID}&queue_next=1"
    )

    headers = {
        "Authorization": f"Bearer {BRIGHTDATA_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = [
        {
            "url": search_url
        }
    ]

    response = httpx.post(
        endpoint,
        headers=headers,
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    print("Bright Data response:")
    print(response.text)

    return response.json()


def search_bookswagon(
    isbn_13: str | None = None,
    isbn_10: str | None = None,
):
    if not isbn_13 and not isbn_10:
        raise ValueError(
            "ISBN-13 or ISBN-10 is required"
        )

    isbn = isbn_13 or isbn_10

    search_url = (
        f"https://www.bookswagon.com/search-books/{isbn}"
    )

    result = trigger_search_collector(search_url)

    collection_id = result["collection_id"]

    return wait_for_collection(collection_id)

def trigger_amazon_collector(url: str):
    if not BRIGHT_DATA_AMAZON_COLLECTOR_ID:
        raise RuntimeError(
            "BRIGHT_DATA_AMAZON_COLLECTOR_ID is not configured"
        )

    endpoint = (
        "https://api.brightdata.com/dca/trigger"
        f"?collector={BRIGHT_DATA_AMAZON_COLLECTOR_ID}&queue_next=1"
    )

    headers = {
        "Authorization": f"Bearer {BRIGHTDATA_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = [
        {
            "url": url
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

def scrape_amazon(url: str):
    if not BRIGHTDATA_API_KEY:
        raise RuntimeError(
            "BRIGHTDATA_API_KEY is not configured"
        )

    if not BRIGHT_DATA_AMAZON_COLLECTOR_ID:
        raise RuntimeError(
            "BRIGHT_DATA_AMAZON_COLLECTOR_ID is not configured"
        )

    result = trigger_amazon_collector(url)

    collection_id = result["collection_id"]

    return wait_for_collection(collection_id)

def trigger_amazon_product_collector(product_url: str):
    if not BRIGHTDATA_API_KEY:
        raise RuntimeError(
            "BRIGHTDATA_API_KEY is not configured"
        )

    if not BRIGHT_DATA_AMAZON_PRODUCT_COLLECTOR_ID:
        raise RuntimeError(
            "BRIGHT_DATA_AMAZON_PRODUCT_COLLECTOR_ID is not configured"
        )

    endpoint = (
        "https://api.brightdata.com/dca/trigger"
        f"?collector={BRIGHT_DATA_AMAZON_PRODUCT_COLLECTOR_ID}"
        "&queue_next=1"
    )

    headers = {
        "Authorization": f"Bearer {BRIGHTDATA_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = [
        {
            "url": product_url
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


def scrape_amazon_product(product_url: str):
    result = trigger_amazon_product_collector(product_url)

    collection_id = result["collection_id"]

    return wait_for_collection(collection_id)

def trigger_flipkart_dataset(book_url: str):
    if not BRIGHTDATA_API_KEY:
        raise RuntimeError("BRIGHTDATA_API_KEY is not configured")

    if not BRIGHT_DATA_FLIPKART_DATASET_ID:
        raise RuntimeError(
            "BRIGHT_DATA_FLIPKART_DATASET_ID is not configured"
        )

    endpoint = (
        "https://api.brightdata.com/datasets/v3/trigger"
        f"?dataset_id={BRIGHT_DATA_FLIPKART_DATASET_ID}"
        "&include_errors=true"
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

def get_flipkart_snapshot(snapshot_id: str):
    if not BRIGHTDATA_API_KEY:
        raise RuntimeError(
            "BRIGHTDATA_API_KEY is not configured"
        )

    url = (
        "https://api.brightdata.com/datasets/v3/snapshot/"
        f"{'sd_mt33x2e0dhl6auuxl'}"
    )

    headers = {
        "Authorization": f"Bearer {BRIGHTDATA_API_KEY}",
    }

    response = httpx.get(
        url,
        headers=headers,
        timeout=60,
    )

    response.raise_for_status()

    return response

def scrape_flipkart(book_url: str):
    result = trigger_flipkart_dataset(book_url)

    snapshot_id = result["snapshot_id"]

    response = get_flipkart_snapshot(snapshot_id)

    if response.status_code != 200:
        raise RuntimeError(
            f"Flipkart snapshot request failed: {response.status_code}"
        )

    return response.json()