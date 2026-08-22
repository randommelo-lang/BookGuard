from brightdata import scrape_book


def scrape(url: str) -> dict:
    """
    Scrape a Bookswagon book listing and return
    the standard BookGuard source response.
    """

    listing = scrape_book(url)

    if not listing:
        return {
            "source": "bookswagon",
            "status": "not_found",
            "message": "No Bookswagon listing was found.",
            "results": [],
        }

    return {
        "source": "bookswagon",
        "status": "success",
        "results": [listing],
    }


def search(
    isbn_13: str | None = None,
    isbn_10: str | None = None,
) -> dict:
    """
    Find a Bookswagon listing using an ISBN.

    Search implementation will be added here.
    """

    if not isbn_13 and not isbn_10:
        return {
            "source": "bookswagon",
            "status": "error",
            "message": "An ISBN-13 or ISBN-10 is required.",
            "results": [],
        }

    return {
        "source": "bookswagon",
        "status": "not_implemented",
        "query": {
            "isbn_13": isbn_13,
            "isbn_10": isbn_10,
        },
        "results": [],
    }