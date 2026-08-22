from brightdata import search_bookswagon
from sources.bookswagon import scrape as scrape_bookswagon
from sources.amazon import search as search_amazon
from sources.flipkart import scrape as scrape_flipkart


def _error_response(
    source: str,
    status: str,
    message: str,
    isbn_13: str | None = None,
    isbn_10: str | None = None,
) -> dict:
    """
    Build a consistent store-search response.
    """

    return {
        "source": source,
        "status": status,
        "message": message,
        "query": {
            "isbn_13": isbn_13,
            "isbn_10": isbn_10,
        },
        "results": [],
    }


def _first_result(
    result: dict | list,
) -> dict | None:
    """
    Return the first result from a store response.
    """

    if isinstance(result, list):
        return result[0] if result and isinstance(result[0], dict) else None

    if isinstance(result, dict):
        results = result.get("results", [])

        if results and isinstance(results, list) and isinstance(results[0], dict):
            return results[0]

        return result

    return None


from normalization import (
    normalize_isbn,
    clean_display_title,
    resolve_isbn_from_title,
)

from live_scraper import (
    scrape_live_amazon,
    scrape_live_flipkart,
    scrape_live_bookswagon,
)


def search_store(
    source: str,
    isbn_13: str | None = None,
    isbn_10: str | None = None,
    product_url: str | None = None,
    title: str | None = None,
    author: str | None = None,
) -> dict:
    """
    Search for a book on a supported marketplace using live web scraping.
    """

    source = source.lower().strip()

    if not isbn_13 and not isbn_10 and title:
        res_13, res_10 = resolve_isbn_from_title(title)
        isbn_13 = isbn_13 or res_13
        isbn_10 = isbn_10 or res_10

    if not isbn_13 and not isbn_10 and not product_url and not title:
        return _error_response(
            source=source,
            status="error",
            message="An ISBN, URL, or title is required.",
            isbn_13=isbn_13,
            isbn_10=isbn_10,
        )

    store_product_url = product_url if (product_url and source in product_url.lower()) else None
    
    if source == "amazon":
        target_query = store_product_url or isbn_10 or isbn_13 or (f"{title} {author or ''}".strip() if title else None)
    elif source == "bookswagon":
        target_query = store_product_url or isbn_13 or isbn_10 or (f"{title} {author or ''}".strip() if title else None)
    elif source == "flipkart":
        target_query = store_product_url or (f"https://www.flipkart.com/book/p/itm?pid={isbn_13}" if isbn_13 else None) or isbn_13 or isbn_10 or (f"{title} {author or ''}".strip() if title else None)
    else:
        target_query = store_product_url or isbn_13 or isbn_10 or (f"{title} {author or ''}".strip() if title else None)

    if not target_query:
        return _error_response(
            source=source,
            status="error",
            message=f"Could not build search query for {source}.",
            isbn_13=isbn_13,
            isbn_10=isbn_10,
        )

    try:
        from self_healing import heal_scrape
        healed_res = heal_scrape(target_query, store=source, title=title, author=author)
        if healed_res and healed_res.get("status") == "success" and healed_res.get("results"):
            return healed_res
    except Exception:
        pass

    return _error_response(
        source=source,
        status="not_found",
        message=f"No matching {source} listing was found.",
        isbn_13=isbn_13,
        isbn_10=isbn_10,
    )

    # --------------------------------
    # Unsupported store
    # --------------------------------

    return _error_response(
        source=source,
        status="not_implemented",
        message=(
            f"Search for {source} "
            "is not implemented yet."
        ),
        isbn_13=isbn_13,
        isbn_10=isbn_10,
    )


def search_all_stores(
    isbn_13: str | None = None,
    isbn_10: str | None = None,
    current_source: str | None = None,
    current_product_url: str | None = None,
    title: str | None = None,
    author: str | None = None,
) -> dict:
    """
    Search all supported marketplaces for the same book.

    The current listing can be supplied so we don't need
    to search the same marketplace again.
    """

    if not isbn_13 and not isbn_10 and not title:
        return {
            "status": "error",
            "message": (
                "An ISBN or book title is required "
                "for marketplace discovery."
            ),
            "results": {},
            "errors": [],
        }

    current_source = (
        current_source.lower().strip()
        if current_source
        else None
    )

    stores = [
        "amazon",
        "flipkart",
        "bookswagon",
    ]

    results = {}
    errors = []

    for store in stores:

        # --------------------------------
        # Use current listing if possible
        # --------------------------------

        if (
            current_source == store
            and current_product_url
        ):
            try:
                result = search_store(
                    source=store,
                    isbn_13=isbn_13,
                    isbn_10=isbn_10,
                    product_url=current_product_url,
                    title=title,
                    author=author,
                )

                results[store] = result

            except Exception as exc:
                errors.append({
                    "source": store,
                    "message": str(exc),
                })

            continue

        # --------------------------------
        # Search other marketplaces
        # --------------------------------

        try:

            result = search_store(
                source=store,
                isbn_13=isbn_13,
                isbn_10=isbn_10,
                title=title,
                author=author,
            )

            if result.get("status") == "success":
                results[store] = result

            else:
                errors.append({
                    "source": store,
                    "message": result.get(
                        "message",
                        "Store search failed.",
                    ),
                    "status": result.get(
                        "status"
                    ),
                })

        except Exception as exc:

            errors.append({
                "source": store,
                "message": str(exc),
            })

    return {
        "status": "success",
        "results": results,
        "errors": errors,
    }