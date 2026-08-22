from brightdata import scrape_flipkart


def _extract_author(description: str | None) -> str | None:
    """
    Extract the author from the Flipkart Library description.

    Expected pattern:
        "Goodbye, Eri by Fujimoto Tatsuki from Flipkart.com."

    Returns only the author portion.
    """

    if not description:
        return None

    marker_start = " by "
    marker_end = " from Flipkart.com"

    if marker_start not in description:
        return None

    author_part = description.split(marker_start, 1)[1]

    if marker_end in author_part:
        author_part = author_part.split(marker_end, 1)[0]

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

    sale_price = raw.get("sale_price")

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
    Scrape and normalize a Flipkart product page.

    Bright Data handles the actual scraping.
    This function converts the returned Dataset record
    into BookGuard's standard listing format.
    """

    raw = scrape_flipkart(url)

    if not raw:
        return {
            "source": "flipkart",
            "status": "error",
            "message": "No data returned from Flipkart.",
            "results": [],
        }

    author = _extract_author(
        raw.get("description")
    )

    price = _extract_price(raw)

    availability = _normalize_availability(
        raw.get("availability")
    )

    isbn_13 = (
        raw.get("item_id")
        or raw.get("group_id")
    )

    return {
        "source": "flipkart",
        "status": "success",
        "results": [
            {
                "book_title": raw.get("title"),
                "author": author,
                "isbn_10": None,
                "isbn_13": isbn_13,
                "publisher": raw.get("brand"),
                "edition": None,
                "price": price,
                "availability": availability,
                "seller_name": raw.get("store_name"),
                "product_url": raw.get("url") or url,
                "store": "Flipkart",
            }
        ],
    }