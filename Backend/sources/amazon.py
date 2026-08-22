from brightdata import scrape_amazon
from brightdata import scrape_amazon_product
from normalization import normalize_isbn


def _normalize_product(record: dict) -> dict:
    """
    Convert an Amazon Bright Data record into the
    standard BookGuard listing format.
    """

    availability = record.get("availability")

    if availability:
        availability_lower = availability.strip().lower()

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

    return {
        "book_title": record.get("book_title"),
        "author": record.get("author"),
        "isbn_10": normalize_isbn(record.get("isbn_10")),
        "isbn_13": normalize_isbn(record.get("isbn_13")),
        "publisher": record.get("publisher"),
        "edition": record.get("edition"),
        "price": record.get("price"),
        "availability": availability,
        "seller_name": record.get("seller_name"),
        "product_url": (
            record.get("product_url")
            or record.get("input", {}).get("url")
        ),
        "store": "Amazon",
    }


def scrape(product_url: str) -> dict:
    """
    Scrape an Amazon product URL.
    """

    records = scrape_amazon_product(product_url)

    if not isinstance(records, list):
        records = [records]

    products = []

    for record in records:
        if not isinstance(record, dict):
            continue

        if record.get("page_type") != "product":
            continue

        products.append(
            _normalize_product(record)
        )

    if not products:
        return {
            "source": "amazon",
            "status": "not_found",
            "message": "No Amazon product listing was found.",
            "results": [],
        }

    return {
        "source": "amazon",
        "status": "success",
        "results": products,
    }


def search(
    isbn_13: str | None = None,
    isbn_10: str | None = None,
) -> dict:
    """
    Search Amazon for a book using ISBN.

    Only a listing matching the requested ISBN is accepted.
    """

    if not isbn_13 and not isbn_10:
        return {
            "source": "amazon",
            "status": "error",
            "message": "An ISBN-13 or ISBN-10 is required.",
            "results": [],
        }

    search_isbn_13 = normalize_isbn(isbn_13)
    search_isbn_10 = normalize_isbn(isbn_10)

    search_url = (
        f"https://www.amazon.in/s?k={isbn_13 or isbn_10}"
    )

    records = scrape_amazon(search_url)

    if not isinstance(records, list):
        records = [records]

    matches = []

    for record in records:
        if not isinstance(record, dict):
            continue

        record_isbn_13 = normalize_isbn(
            record.get("isbn_13")
        )

        record_isbn_10 = normalize_isbn(
            record.get("isbn_10")
        )

        isbn_13_match = (
            search_isbn_13
            and record_isbn_13
            and record_isbn_13 == search_isbn_13
        )

        isbn_10_match = (
            search_isbn_10
            and record_isbn_10
            and record_isbn_10 == search_isbn_10
        )

        if isbn_13_match or isbn_10_match:
            matches.append(
                _normalize_product(record)
            )

    if not matches:
        return {
            "source": "amazon",
            "status": "not_found",
            "message": "No Amazon listing matched the supplied ISBN.",
            "results": [],
        }

    return {
        "source": "amazon",
        "status": "success",
        "results": matches,
    }