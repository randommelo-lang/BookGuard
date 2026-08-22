import re
from brightdata import scrape_flipkart


def _extract_author(raw: dict) -> str | None:
    """
    Extract author from Flipkart record or description.
    """
    if raw.get("author"):
        return raw.get("author")

    description = raw.get("description")
    if not description:
        return None

    marker_start = " by "
    if marker_start not in description:
        return None

    author_part = description.split(marker_start, 1)[1]

    for end_marker in [
        " from Flipkart.com",
        " online at best price",
        " at Flipkart.com",
        " online at",
    ]:
        if end_marker in author_part:
            author_part = author_part.split(end_marker, 1)[0]

    author_part = author_part.strip()
    return author_part or None


def _normalize_availability(value: str | None) -> str | None:
    """
    Convert Bright Data availability into BookGuard's format.
    """

    if not value:
        return None

    value = value.strip().lower()

    if value in {
        "in_stock",
        "in stock",
        "available",
    }:
        return "In Stock"

    if value in {
        "out_of_stock",
        "out of stock",
        "unavailable",
        "not_available",
    }:
        return "Unavailable"

    return None


def _extract_price(raw: dict) -> dict | None:
    """
    Convert Flipkart sale_price into BookGuard's price structure.
    """

    sale_price = raw.get("sale_price") or raw.get("price")

    if not sale_price:
        return None

    if isinstance(sale_price, (int, float)):
        return {
            "value": float(sale_price),
            "currency": "INR",
            "symbol": "₹",
        }

    if isinstance(sale_price, str):
        cleaned = (
            sale_price
            .replace("₹", "")
            .replace(",", "")
            .strip()
        )

        try:
            return {
                "value": float(cleaned),
                "currency": "INR",
                "symbol": "₹",
            }
        except ValueError:
            return None

    return None


def scrape(url: str) -> dict:
    """
    Scrape and normalize a Flipkart product page using live web scraping.
    """

    try:
        raw = scrape_flipkart(url)

        if raw and isinstance(raw, dict) and (raw.get("title") or raw.get("description")):
            author = _extract_author(raw)
            price = _extract_price(raw)
            availability = _normalize_availability(
                raw.get("availability")
            )

            isbn_candidate = (
                raw.get("isbn")
                or raw.get("isbn_13")
                or raw.get("isbn13")
            )

            if not isbn_candidate:
                item_id = str(
                    raw.get("item_id")
                    or raw.get("group_id")
                    or ""
                )
                digits_only = re.sub(r"[^\d]", "", item_id)
                if len(digits_only) == 13 and (
                    digits_only.startswith("978")
                    or digits_only.startswith("979")
                ):
                    isbn_candidate = digits_only
                else:
                    isbn_candidate = None

            return {
                "source": "flipkart",
                "status": "success",
                "results": [
                    {
                        "book_title": raw.get("title"),
                        "author": author,
                        "isbn_10": raw.get("isbn_10") or raw.get("isbn10"),
                        "isbn_13": isbn_candidate,
                        "publisher": raw.get("brand") or raw.get("publisher"),
                        "edition": raw.get("edition"),
                        "price": price,
                        "availability": availability,
                        "seller_name": raw.get("store_name") or raw.get("seller_name"),
                        "product_url": raw.get("url") or url,
                        "store": "Flipkart",
                    }
                ],
            }
    except Exception:
        pass

    from live_scraper import scrape_live_flipkart
    live_data = scrape_live_flipkart(url)
    if live_data:
        return {
            "source": "flipkart",
            "status": "success",
            "results": [live_data],
        }

    return {
        "source": "flipkart",
        "status": "error",
        "message": "Failed to scrape Flipkart listing.",
        "results": [],
    }