from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from validator import validate_book
from analyzer import analyze_book
from comparison import compare_listings
from normalization import normalize_listing
from source_detector import detect_source

from sources.bookswagon import scrape as scrape_bookswagon
from sources.amazon import scrape as scrape_amazon
from sources.flipkart import scrape as scrape_flipkart
from sources.generic import scrape as scrape_generic


app = FastAPI(title="BookGuard API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    url: str
    compare_urls: list[str] = []


class CompareRequest(BaseModel):
    urls: list[str]


class AutoCompareRequest(BaseModel):
    url: str | None = None
    isbn_13: str | None = None
    isbn_10: str | None = None


@app.get("/api/health")
def health():
    return {
        "status": "ok"
    }


def scrape_source(url: str) -> tuple[str, dict]:
    """
    Detect and scrape a marketplace URL using Bright Data Self-Healing Engine.
    """

    source = detect_source(url)

    try:
        from self_healing import heal_scrape
        data = heal_scrape(url_or_query=url, store=source)
        if data and data.get("status") == "success" and data.get("results"):
            return source, data
    except HTTPException:
        raise
    except Exception:
        pass

    try:
        if source == "bookswagon":
            data = scrape_bookswagon(url)
        elif source == "amazon":
            data = scrape_amazon(url)
        elif source == "flipkart":
            data = scrape_flipkart(url)
        elif source == "other":
            data = scrape_generic(url)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported source: {source}",
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": f"Scraping failure for {source}: {str(exc)}",
                "source": source,
            },
        )

    return source, data


def extract_listing(
    source: str,
    data: dict,
) -> dict:
    """
    Extract and normalize the first marketplace listing.
    """

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Invalid response payload from scraper.",
                "source": source,
            },
        )

    results = data.get("results", [])

    if not results or not isinstance(results[0], dict):
        raise HTTPException(
            status_code=404,
            detail={
                "message": "No book listing was found.",
                "source": source,
            },
        )

    listing = normalize_listing(results[0])

    # Make sure comparison.py knows the marketplace.
    listing["source"] = source

    return listing


def build_comparison(
    urls: list[str],
) -> tuple[dict, list[dict]]:
    """
    Scrape multiple marketplace URLs and compare
    the resulting listings.

    Failed individual stores are returned as errors
    instead of causing the whole comparison to fail.
    """

    listings = []
    errors = []

    for url in urls:

        try:
            source, data = scrape_source(url)

            listing = extract_listing(
                source,
                data,
            )

            listings.append(listing)

        except HTTPException as exc:

            errors.append({
                "url": url,
                "error": exc.detail,
            })

        except Exception as exc:

            errors.append({
                "url": url,
                "error": str(exc),
            })

    if not listings:
        return (
            {
                "sources": [],
                "identity": {},
                "price": {},
                "differences": [],
            },
            errors,
        )

    comparison = compare_listings(
        listings
    )

    return comparison, errors


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest):

    # --------------------------------
    # Scrape submitted marketplace
    # --------------------------------

    source, data = scrape_source(
        request.url
    )

    listing = extract_listing(
        source,
        data,
    )

    # --------------------------------
    # Validate submitted listing
    # --------------------------------

    validation = validate_book(
        listing
    )

    if not validation["valid"]:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Incomplete book listing data",
                "validation": validation,
            },
        )

    # --------------------------------
    # Optional cross-market comparison
    # --------------------------------

    comparison = None
    comparison_errors = []

    if request.compare_urls:

        # Make sure the submitted URL is included.
        comparison_urls = list(
            request.compare_urls
        )

        if request.url not in comparison_urls:
            comparison_urls.insert(
                0,
                request.url,
            )

        if len(comparison_urls) > 10:
            raise HTTPException(
                status_code=400,
                detail="A maximum of 10 comparison URLs is allowed.",
            )

        comparison, comparison_errors = (
            build_comparison(
                comparison_urls
            )
        )

    elif listing.get("isbn_13") or listing.get("isbn_10") or listing.get("book_title"):
        try:
            from store_search import search_all_stores
            discovery = search_all_stores(
                isbn_13=listing.get("isbn_13"),
                isbn_10=listing.get("isbn_10"),
                current_source=source,
                current_product_url=request.url,
                title=listing.get("book_title"),
                author=listing.get("author"),
            )
            discovered_listings = [listing]
            for store_name, store_res in discovery.get("results", {}).items():
                results = store_res.get("results", [])
                if results and isinstance(results[0], dict):
                    discovered_listings.append(normalize_listing(results[0]))

            if len(discovered_listings) > 1:
                comparison = compare_listings(discovered_listings)
                comparison_errors = discovery.get("errors", [])
        except Exception:
            pass

    # --------------------------------
    # Analyze listing
    # --------------------------------

    analysis = analyze_book(
        listing,
        comparison=comparison,
    )

    return {
        "status": "success",
        "source": source,
        "data": listing,
        "analysis": analysis,
        "comparison": comparison,
        "comparison_errors": comparison_errors,
        "healing_meta": data.get("healing_meta") or listing.get("healing_meta"),
    }


@app.post("/api/compare")
def compare(request: CompareRequest):

    if not request.urls:
        raise HTTPException(
            status_code=400,
            detail="At least one marketplace URL is required.",
        )

    if len(request.urls) > 10:
        raise HTTPException(
            status_code=400,
            detail="A maximum of 10 URLs can be compared.",
        )

    comparison, errors = build_comparison(
        request.urls
    )

    if not comparison["sources"]:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "No marketplace listings could be compared.",
                "errors": errors,
            },
        )

    return {
        "status": "success",
        "comparison": comparison,
        "errors": errors,
    }


@app.post("/api/auto-compare")
def auto_compare(request: AutoCompareRequest):
    """
    Auto-discover peer listings on Amazon, Flipkart, and Bookswagon
    using ISBN or URL and return comprehensive cross-marketplace risk analysis.
    """
    from store_search import search_all_stores

    if not request.url and not request.isbn_13 and not request.isbn_10:
        raise HTTPException(
            status_code=400,
            detail="A book URL or ISBN is required for auto-comparison.",
        )

    primary_listing = None
    current_source = None
    isbn_13 = request.isbn_13
    isbn_10 = request.isbn_10

    if request.url:
        current_source, data = scrape_source(request.url)
        primary_listing = extract_listing(current_source, data)
        isbn_13 = isbn_13 or primary_listing.get("isbn_13")
        isbn_10 = isbn_10 or primary_listing.get("isbn_10")

    if not isbn_13 and not isbn_10:
        comparison = compare_listings([primary_listing])
        analysis = analyze_book(primary_listing, comparison=comparison)
        return {
            "status": "success",
            "source": current_source or "unknown",
            "data": primary_listing,
            "analysis": analysis,
            "comparison": comparison,
            "comparison_errors": [
                "Could not extract ISBN from listing URL for peer discovery. Missing ISBN flagged as High Risk."
            ],
        }

    discovery = search_all_stores(
        isbn_13=isbn_13,
        isbn_10=isbn_10,
        current_source=current_source,
        current_product_url=request.url,
        title=primary_listing.get("book_title") if primary_listing else None,
        author=primary_listing.get("author") if primary_listing else None,
    )

    discovered_listings = []
    if primary_listing:
        discovered_listings.append(primary_listing)

    for store_name, store_res in discovery.get("results", {}).items():
        results = store_res.get("results", [])
        if results and isinstance(results[0], dict):
            disc_listing = normalize_listing(results[0])
            # Avoid duplicate entries if primary_listing already covers this store
            disc_store = disc_listing.get("store") or disc_listing.get("source") or ""
            if not any((d.get("store") or d.get("source") or "").lower() == disc_store.lower() for d in discovered_listings):
                discovered_listings.append(disc_listing)

    comparison = None
    if discovered_listings:
        comparison = compare_listings(discovered_listings)

    analysis = None
    if primary_listing:
        analysis = analyze_book(primary_listing, comparison=comparison)
    elif discovered_listings:
        analysis = analyze_book(discovered_listings[0], comparison=comparison)

    return {
        "status": "success",
        "primary_listing": primary_listing,
        "discovered_listings": discovered_listings,
        "analysis": analysis,
        "comparison": comparison,
        "discovery_errors": discovery.get("errors", []),
    }