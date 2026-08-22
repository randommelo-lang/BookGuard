import os
import time
import json
from urllib.parse import quote_plus

import httpx
from dotenv import load_dotenv


load_dotenv()


# ============================================================
# Environment
# ============================================================

BRIGHTDATA_API_KEY = os.getenv(
    "BRIGHTDATA_API_KEY"
)

BRIGHT_DATA_COLLECTOR_ID = os.getenv(
    "BRIGHT_DATA_COLLECTOR_ID"
)

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

BRIGHT_DATA_FLIPKART_PRODUCT_COLLECTOR_ID = os.getenv(
    "BRIGHT_DATA_FLIPKART_PRODUCT_COLLECTOR_ID",
    BRIGHT_DATA_FLIPKART_DATASET_ID,
)


# ============================================================
# Common helpers
# ============================================================

def _require_api_key():
    if not BRIGHTDATA_API_KEY:
        raise RuntimeError(
            "BRIGHTDATA_API_KEY is not configured"
        )


def _headers(json_content: bool = False):
    headers = {
        "Authorization": (
            f"Bearer {BRIGHTDATA_API_KEY}"
        ),
    }

    if json_content:
        headers["Content-Type"] = (
            "application/json"
        )

    return headers


# ============================================================
# Generic Bright Data collector
# ============================================================

def trigger_collector(book_url: str):
    _require_api_key()

    if not BRIGHT_DATA_COLLECTOR_ID:
        raise RuntimeError(
            "BRIGHT_DATA_COLLECTOR_ID is not configured"
        )

    endpoint = (
        "https://api.brightdata.com/dca/trigger"
        f"?collector={BRIGHT_DATA_COLLECTOR_ID}"
        "&queue_next=1"
    )

    payload = [
        {
            "url": book_url
        }
    ]

    response = httpx.post(
        endpoint,
        headers=_headers(json_content=True),
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    return response.json()


def get_collection(collection_id: str):
    _require_api_key()

    if not collection_id:
        raise ValueError(
            "collection_id is required"
        )

    url = (
        "https://api.brightdata.com/dca/dataset"
    )

    params = {
        "id": collection_id,
    }

    response = httpx.get(
        url,
        headers=_headers(),
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

    # JSON Lines response
    records = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        try:
            records.append(
                json.loads(line)
            )
        except ValueError:
            continue

    if records:
        return records

    raise ValueError(
        "Bright Data returned an invalid JSON response"
    )


def wait_for_collection(
    collection_id: str,
    interval: int = 10,
    timeout: int = 300,
):
    """
    Wait for a DCA collection to finish.

    Unlike the old implementation, this has a timeout
    so a broken collector cannot hang BookGuard forever.
    """

    started_at = time.time()

    while True:

        if time.time() - started_at > timeout:
            raise TimeoutError(
                "Bright Data collection timed out"
            )

        result = get_collection(
            collection_id
        )

        # Completed collection containing
        # multiple records.
        if isinstance(result, list):
            print(
                f"Collection returned "
                f"{len(result)} records"
            )
            return result

        status = result.get("status")

        if status:
            print(
                f"Collection status: {status}"
            )

        if status in {
            "collecting",
            "building",
            "pending",
            "running",
        }:
            time.sleep(interval)
            continue

        return result


def scrape_book(book_url: str):
    result = trigger_collector(
        book_url
    )

    collection_id = result.get(
        "collection_id"
    )

    if not collection_id:
        raise RuntimeError(
            "Bright Data collector did not "
            "return a collection_id"
        )

    return wait_for_collection(
        collection_id
    )


# ============================================================
# Search collector
# ============================================================

def trigger_search_collector(
    search_url: str
):
    _require_api_key()

    if not BRIGHT_DATA_SEARCH_COLLECTOR_ID:
        raise RuntimeError(
            "BRIGHT_DATA_SEARCH_COLLECTOR_ID "
            "is not configured"
        )

    endpoint = (
        "https://api.brightdata.com/dca/trigger"
        f"?collector={BRIGHT_DATA_SEARCH_COLLECTOR_ID}"
        "&queue_next=1"
    )

    payload = [
        {
            "url": search_url
        }
    ]

    response = httpx.post(
        endpoint,
        headers=_headers(json_content=True),
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    print(
        "Bright Data search response:"
    )
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
        "https://www.bookswagon.com/search-books/"
        f"{isbn}"
    )

    result = trigger_search_collector(
        search_url
    )

    collection_id = result.get(
        "collection_id"
    )

    if not collection_id:
        raise RuntimeError(
            "Bookswagon search collector did not "
            "return a collection_id"
        )

    return wait_for_collection(
        collection_id
    )


# ============================================================
# Amazon collector
# ============================================================

def trigger_amazon_collector(
    url: str
):
    _require_api_key()

    if not BRIGHT_DATA_AMAZON_COLLECTOR_ID:
        raise RuntimeError(
            "BRIGHT_DATA_AMAZON_COLLECTOR_ID "
            "is not configured"
        )

    endpoint = (
        "https://api.brightdata.com/dca/trigger"
        f"?collector={BRIGHT_DATA_AMAZON_COLLECTOR_ID}"
        "&queue_next=1"
    )

    payload = [
        {
            "url": url
        }
    ]

    response = httpx.post(
        endpoint,
        headers=_headers(json_content=True),
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    return response.json()


def scrape_amazon(url: str):
    result = trigger_amazon_collector(
        url
    )

    collection_id = result.get(
        "collection_id"
    )

    if not collection_id:
        raise RuntimeError(
            "Amazon collector did not "
            "return a collection_id"
        )

    return wait_for_collection(
        collection_id
    )


# ============================================================
# Amazon product collector
# ============================================================

def trigger_amazon_product_collector(
    product_url: str
):
    _require_api_key()

    if not BRIGHT_DATA_AMAZON_PRODUCT_COLLECTOR_ID:
        raise RuntimeError(
            "BRIGHT_DATA_AMAZON_PRODUCT_COLLECTOR_ID "
            "is not configured"
        )

    endpoint = (
        "https://api.brightdata.com/dca/trigger"
        f"?collector={BRIGHT_DATA_AMAZON_PRODUCT_COLLECTOR_ID}"
        "&queue_next=1"
    )

    payload = [
        {
            "url": product_url
        }
    ]

    response = httpx.post(
        endpoint,
        headers=_headers(json_content=True),
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    return response.json()


def scrape_amazon_product(
    product_url: str
):
    result = (
        trigger_amazon_product_collector(
            product_url
        )
    )

    collection_id = result.get(
        "collection_id"
    )

    if not collection_id:
        raise RuntimeError(
            "Amazon product collector did not "
            "return a collection_id"
        )

    return wait_for_collection(
        collection_id
    )


# ============================================================
# Flipkart product dataset
# ============================================================

def trigger_flipkart_dataset(
    book_url: str
):
    _require_api_key()

    flipkart_id = BRIGHT_DATA_FLIPKART_PRODUCT_COLLECTOR_ID or BRIGHT_DATA_FLIPKART_DATASET_ID

    if not flipkart_id:
        raise RuntimeError(
            "BRIGHT_DATA_FLIPKART_PRODUCT_COLLECTOR_ID or "
            "BRIGHT_DATA_FLIPKART_DATASET_ID is not configured"
        )

    endpoint = (
        "https://api.brightdata.com/datasets/v3/trigger"
        f"?dataset_id={flipkart_id}"
        "&include_errors=true"
    )

    payload = [
        {
            "url": book_url
        }
    ]

    response = httpx.post(
        endpoint,
        headers=_headers(json_content=True),
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    return response.json()


def get_flipkart_snapshot(
    snapshot_id: str
):
    """
    Retrieve the exact snapshot returned by
    the Flipkart dataset trigger.
    """

    _require_api_key()

    if not snapshot_id:
        raise ValueError(
            "snapshot_id is required"
        )

    url = (
        "https://api.brightdata.com/"
        "datasets/v3/snapshot/"
        f"{snapshot_id}"
    )

    response = httpx.get(
        url,
        headers=_headers(),
        timeout=60,
    )

    return response


def wait_for_flipkart_snapshot(
    snapshot_id: str,
    interval: int = 5,
    timeout: int = 120,
):
    """
    Poll Flipkart dataset snapshot status until ready.
    """
    started_at = time.time()
    while True:
        if time.time() - started_at > timeout:
            raise TimeoutError("Flipkart snapshot timed out")

        response = get_flipkart_snapshot(snapshot_id)
        if response.status_code == 200:
            try:
                data = response.json()
                if data:
                    if isinstance(data, list):
                        return data[0] if data else {}
                    return data
            except ValueError:
                pass

        time.sleep(interval)


def scrape_flipkart(
    book_url: str
):
    result = trigger_flipkart_dataset(
        book_url
    )

    snapshot_id = result.get(
        "snapshot_id"
    )

    if not snapshot_id:
        raise RuntimeError(
            "Flipkart dataset did not "
            "return a snapshot_id"
        )

    return wait_for_flipkart_snapshot(
        snapshot_id
    )


# ============================================================
# Flipkart discovery
# ============================================================

def _extract_product_urls(
    data
) -> list[str]:
    """
    Extract product URLs from common Bright Data
    search-result response shapes.
    """

    urls = []

    if isinstance(data, dict):

        # Direct product URL
        direct_url = data.get(
            "product_url"
        )

        if direct_url:
            urls.append(direct_url)

        # Common URL fields
        for field in [
            "url",
            "link",
            "product_link",
            "href",
        ]:
            value = data.get(field)

            if (
                isinstance(value, str)
                and "flipkart.com" in value
            ):
                urls.append(value)

        # Nested results
        for field in [
            "results",
            "items",
            "products",
            "data",
        ]:
            nested = data.get(field)

            if nested:
                urls.extend(
                    _extract_product_urls(
                        nested
                    )
                )

    elif isinstance(data, list):

        for item in data:
            urls.extend(
                _extract_product_urls(item)
            )

    # De-duplicate while preserving order
    unique_urls = []

    for url in urls:

        if not isinstance(url, str):
            continue

        if "flipkart.com" not in url:
            continue

        if url not in unique_urls:
            unique_urls.append(url)

    return unique_urls


def _candidate_matches_isbn(
    product_url: str,
    isbn_13: str | None,
    isbn_10: str | None,
) -> bool:
    """
    Quick URL-level ISBN check.
    """

    if not isbn_13 and not isbn_10:
        return True

    if isbn_13 and isbn_13 in product_url:
        return True

    if isbn_10 and isbn_10 in product_url:
        return True

    return False


def search_flipkart(
    title: str | None = None,
    author: str | None = None,
    isbn_13: str | None = None,
    isbn_10: str | None = None,
) -> dict:
    """
    Discover a Flipkart product using title + author (Flipkart search does not index ISBNs reliably).
    """

    if title:
        clean_title = re.sub(r"[^\w\s]", " ", title).strip()
        query_term = f"{clean_title} {author or ''}".strip()
    else:
        query_term = isbn_13 or isbn_10

    if not query_term:
        return {
            "source": "flipkart",
            "status": "error",
            "message": (
                "Title or ISBN is required for "
                "Flipkart search."
            ),
            "results": [],
        }

    # ----------------------------------------
    # Search URL (Category sid=bks for Books)
    # ----------------------------------------

    search_url = (
        "https://www.flipkart.com/search"
        f"?q={quote_plus(query_term)}&sid=bks"
    )

    try:

        result = trigger_search_collector(
            search_url
        )

        collection_id = result.get(
            "collection_id"
        )

        if not collection_id:
            return {
                "source": "flipkart",
                "status": "error",
                "message": (
                    "Flipkart search collector "
                    "did not return a collection_id."
                ),
                "results": [],
            }

        data = wait_for_collection(
            collection_id
        )

    except Exception as exc:

        return {
            "source": "flipkart",
            "status": "error",
            "message": (
                "Flipkart search collector failed: "
                f"{exc}"
            ),
            "results": [],
        }

    # ----------------------------------------
    # Extract candidate product URLs
    # ----------------------------------------

    product_urls = _extract_product_urls(
        data
    )

    if not product_urls:
        return {
            "source": "flipkart",
            "status": "not_found",
            "message": (
                "Flipkart search returned "
                "no product URLs."
            ),
            "results": [],
        }

    # ----------------------------------------
    # Prefer candidates whose URL contains the ISBN
    # ----------------------------------------

    matching_urls = [
        url
        for url in product_urls
        if _candidate_matches_isbn(
            url,
            isbn_13,
            isbn_10,
        )
    ]

    if matching_urls:

        product_url = matching_urls[0]

        return {
            "source": "flipkart",
            "status": "success",
            "product_url": product_url,
            "results": [
                {
                    "product_url": product_url
                }
            ],
        }

    return {
        "source": "flipkart",
        "status": "success",
        "product_url": product_urls[0],
        "candidates": product_urls[:10],
        "results": [
            {
                "product_url": product_urls[0]
            }
        ],
    }