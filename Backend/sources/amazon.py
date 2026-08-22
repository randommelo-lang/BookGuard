from brightdata import scrape_amazon
from brightdata import scrape_amazon_product
from normalization import normalize_isbn


import re


def _extract_price(record: dict) -> dict | None:
    raw_price = record.get("price")
    if raw_price is None:
        return None

    if isinstance(raw_price, dict):
        val = raw_price.get("value")
        if val is not None:
            try:
                return {
                    "value": float(val),
                    "currency": raw_price.get("currency", "INR"),
                    "symbol": raw_price.get("symbol", "₹"),
                }
            except (TypeError, ValueError):
                return None
        return None

    if isinstance(raw_price, (int, float)):
        return {
            "value": float(raw_price),
            "currency": "INR",
            "symbol": "₹",
        }

    if isinstance(raw_price, str):
        cleaned = re.sub(r"[^\d.]", "", raw_price.replace(",", ""))
        if cleaned:
            try:
                return {
                    "value": float(cleaned),
                    "currency": "INR",
                    "symbol": "₹",
                }
            except ValueError:
                return None

    return None


def _normalize_product(record: dict, url_fallback: str | None = None) -> dict:
    """
    Convert an Amazon Bright Data record into the
    standard BookGuard listing format.
    """

    availability = record.get("availability")

    if availability:
        availability_lower = str(availability).strip().lower()

        if availability_lower in {
            "in stock",
            "in_stock",
            "available",
        }:
            availability = "In Stock"

        elif availability_lower in {
            "unavailable",
            "out of stock",
            "out_of_stock",
        }:
            availability = "Unavailable"

    isbn_13 = normalize_isbn(record.get("isbn_13") or record.get("isbn13"))
    isbn_10 = normalize_isbn(record.get("isbn_10") or record.get("isbn10") or record.get("asin"))

    target_url = (
        record.get("product_url")
        or record.get("url")
        or record.get("input", {}).get("url")
        or url_fallback
    )

    if not isbn_13 and target_url:
        match_isbn = re.search(r"(978\d{10}|979\d{10})", target_url)
        if match_isbn:
            isbn_13 = match_isbn.group(1)

    return {
        "book_title": (
            record.get("book_title")
            or record.get("title")
            or record.get("name")
            or record.get("product_title")
        ),
        "author": (
            record.get("author")
            or record.get("by_author")
            or record.get("author_name")
        ),
        "isbn_10": isbn_10,
        "isbn_13": isbn_13,
        "publisher": record.get("publisher") or record.get("brand"),
        "edition": record.get("edition") or record.get("format") or record.get("binding"),
        "price": _extract_price(record),
        "availability": availability or "In Stock",
        "seller_name": record.get("seller_name") or record.get("seller") or "Amazon",
        "product_url": target_url,
        "store": "Amazon",
    }


def scrape(product_url: str) -> dict:
    """
    Scrape an Amazon product or search URL using live web scraping.
    """
    try:
        is_search_url = "/s?" in product_url or "/s/" in product_url

        if is_search_url:
            records = scrape_amazon(product_url)
        else:
            records = scrape_amazon_product(product_url)

        if not isinstance(records, list):
            records = [records]

        products = []

        for record in records:
            if not isinstance(record, dict):
                continue

            if not is_search_url and record.get("page_type") and record.get("page_type") != "product":
                continue

            normalized = _normalize_product(record, url_fallback=product_url)
            if normalized.get("book_title") or normalized.get("isbn_13"):
                products.append(normalized)

        if products:
            return {
                "source": "amazon",
                "status": "success",
                "results": products,
            }
    except Exception:
        pass

    from live_scraper import scrape_live_amazon
    live_data = scrape_live_amazon(product_url)
    if live_data:
        return {
            "source": "amazon",
            "status": "success",
            "results": [live_data],
        }

    return {
        "source": "amazon",
        "status": "error",
        "message": "Failed to scrape Amazon listing.",
        "results": [],
    }


def search(
    isbn_13: str | None = None,
    isbn_10: str | None = None,
) -> dict:
    """
    Search Amazon for a book using strict ISBN lookup.
    """

    if not isbn_13 and not isbn_10:
        return {
            "source": "amazon",
            "status": "error",
            "message": "An ISBN-13 or ISBN-10 is required.",
            "results": [],
        }

    from live_scraper import scrape_live_amazon, isbn13_to_isbn10

    target_query = isbn_10 or (isbn13_to_isbn10(isbn_13) if isbn_13 else None) or isbn_13

    try:
        live_res = scrape_live_amazon(target_query)
        if live_res:
            return {
                "source": "amazon",
                "status": "success",
                "results": [live_res],
            }
    except Exception:
        pass

    return {
        "source": "amazon",
        "status": "not_found",
        "message": "No Amazon listing matched the supplied ISBN.",
        "results": [],
    }