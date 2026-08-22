from normalization import normalize_listing

def compare_listings(listings: list[dict]) -> dict:
    """
    Compare marketplace listings as peer sources.

    No marketplace is treated as the source of truth.
    The function reports agreements, differences, and price ranges.
    """

    if not listings:
        return {
            "sources": [],
            "identity": {},
            "price": {},
            "differences": [],
        }

    normalized_listings = [
        normalize_listing(listing)
        for listing in listings
    ]

    sources = [
        listing.get("source")
        for listing in listings
        if listing.get("source")
    ]

    # -------------------------
    # Identity comparison
    # -------------------------

    identity = {}

    for field in [
        "isbn_10",
        "isbn_13",
        "book_title",
        "author",
        "publisher",
        "edition",
    ]:
        values = {}

        for listing in normalized_listings:
            value = listing.get(field)

            if value:
                source = listing.get("source", "unknown")
                values[source] = value

        unique_values = set(values.values())

        if not values:
            status = "unavailable"
        elif len(unique_values) == 1:
            status = "agreement"
        else:
            status = "disagreement"

        identity[field] = {
            "status": status,
            "values": values,
        }

    # -------------------------
    # Price comparison
    # -------------------------

    prices = {}

    for listing in listings:
        price = listing.get("price")

        if isinstance(price, dict) and price.get("value") is not None:
            source = listing.get("source", "unknown")
            prices[source] = price["value"]

    if prices:
        price_values = list(prices.values())

        price_info = {
            "status": "available",
            "values": prices,
            "min": min(price_values),
            "max": max(price_values),
            "difference": max(price_values) - min(price_values),
        }
    else:
        price_info = {
            "status": "unavailable",
            "values": {},
            "min": None,
            "max": None,
            "difference": None,
        }

    # -------------------------
    # Differences
    # -------------------------

    differences = []

    for field, result in identity.items():
        if result["status"] == "disagreement":
            differences.append({
                "field": field,
                "type": "metadata_disagreement",
                "values": result["values"],
            })

    return {
        "sources": sources,
        "identity": identity,
        "price": price_info,
        "differences": differences,
    }