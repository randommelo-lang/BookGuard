from brightdata import search_bookswagon
from sources.bookswagon import scrape as scrape_bookswagon
from sources.amazon import search as search_amazon
from sources.flipkart import scrape as scrape_flipkart


def search_store(
    source: str,
    isbn_13: str | None = None,
    isbn_10: str | None = None,
    product_url: str | None = None,
) -> dict:
    """
    Search for a book on a supported marketplace.

    The search returns a normalized marketplace listing.
    """

    source = source.lower().strip()

    # Flipkart currently requires a product URL.
    if source == "flipkart":
        if not product_url:
            return {
                "source": source,
                "status": "not_implemented",
                "message": (
                    "Flipkart search by ISBN is not implemented yet. "
                    "A product URL is required."
                ),
                "query": {
                    "isbn_13": isbn_13,
                    "isbn_10": isbn_10,
                },
                "results": [],
            }

        return scrape_flipkart(product_url)

    # Amazon and Bookswagon require an ISBN.
    if not isbn_13 and not isbn_10:
        return {
            "source": source,
            "status": "error",
            "message": "An ISBN-13 or ISBN-10 is required.",
            "results": [],
        }

    if source == "bookswagon":
        search_result = search_bookswagon(
            isbn_13=isbn_13,
            isbn_10=isbn_10,
        )

        product_url = search_result.get("product_url")

        if not product_url:
            return {
                "source": source,
                "status": "not_found",
                "message": "No matching Bookswagon listing was found.",
                "results": [],
            }

        listing = scrape_bookswagon(product_url)

        return {
            "source": source,
            "status": "success",
            "results": [listing],
        }

    if source == "amazon":
        return search_amazon(
            isbn_13=isbn_13,
            isbn_10=isbn_10,
        )

    return {
        "source": source,
        "status": "not_implemented",
        "message": f"Search for {source} is not implemented yet.",
        "query": {
            "isbn_13": isbn_13,
            "isbn_10": isbn_10,
        },
        "results": [],
    }