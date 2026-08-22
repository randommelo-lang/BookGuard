from normalization import normalize_listing


def compare_listings(listings: list[dict]) -> dict:
    """
    Compare marketplace listings as peer sources.

    No marketplace is treated as the source of truth.
    The function reports agreements, differences,
    price ranges, and price anomalies.
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
        for listing in normalized_listings
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
            norm_key = f"normalized_{field}"
            value = listing.get(norm_key) or listing.get(field)

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

    for listing in normalized_listings:
        price = listing.get("price")

        if isinstance(price, dict) and price.get("value") is not None:
            source = (listing.get("store") or listing.get("source") or "Marketplace").strip().capitalize()

            try:
                prices[source] = float(price["value"])
            except (TypeError, ValueError):
                continue

    if prices:
        price_values = list(prices.values())

        sorted_prices = sorted(price_values)

        midpoint = len(sorted_prices) // 2

        if len(sorted_prices) % 2 == 0:
            median_price = (
                sorted_prices[midpoint - 1]
                + sorted_prices[midpoint]
            ) / 2
        else:
            median_price = sorted_prices[midpoint]

        anomalies = []

        # Price anomaly detection requires at least
        # two marketplace prices.
        if len(price_values) >= 2 and median_price > 0:

            for source, price in prices.items():

                difference_from_median = (
                    median_price - price
                )

                percentage_below_median = (
                    difference_from_median
                    / median_price
                ) * 100

                # ---------------------------------
                # Critical price anomaly (>= 85% below median)
                # ---------------------------------

                if percentage_below_median >= 85:

                    anomalies.append({
                        "source": source,
                        "type": "price_anomaly",
                        "severity": "critical",
                        "points": 70,
                        "price": price,
                        "median_price": median_price,
                        "percentage_below_median": round(
                            percentage_below_median,
                            2,
                        ),
                        "message": (
                            "Listing price is extremely "
                            "below comparable marketplace prices."
                        ),
                    })

                # ---------------------------------
                # Critical price anomaly (>= 70% below median)
                # ---------------------------------

                elif percentage_below_median >= 70:

                    anomalies.append({
                        "source": source,
                        "type": "price_anomaly",
                        "severity": "critical",
                        "points": 55,
                        "price": price,
                        "median_price": median_price,
                        "percentage_below_median": round(
                            percentage_below_median,
                            2,
                        ),
                        "message": (
                            "Listing price is substantially "
                            "below comparable marketplace prices."
                        ),
                    })

                # ---------------------------------
                # High price anomaly (>= 50% below median)
                # ---------------------------------

                elif percentage_below_median >= 50:

                    anomalies.append({
                        "source": source,
                        "type": "price_anomaly",
                        "severity": "high",
                        "points": 45,
                        "price": price,
                        "median_price": median_price,
                        "percentage_below_median": round(
                            percentage_below_median,
                            2,
                        ),
                        "message": (
                            "Listing price is significantly "
                            "below comparable marketplace prices."
                        ),
                    })

                # ---------------------------------
                # Medium price anomaly (>= 30% below median)
                # ---------------------------------

                elif percentage_below_median >= 30:

                    anomalies.append({
                        "source": source,
                        "type": "price_anomaly",
                        "severity": "medium",
                        "points": 25,
                        "price": price,
                        "median_price": median_price,
                        "percentage_below_median": round(
                            percentage_below_median,
                            2,
                        ),
                        "message": (
                            "Listing price is moderately "
                            "below comparable marketplace prices."
                        ),
                    })

        price_urls = {}
        for listing in normalized_listings:
            st = (listing.get("store") or listing.get("source") or "Marketplace").strip().capitalize()
            p_url = listing.get("product_url")
            if p_url:
                price_urls[st] = p_url

        price_info = {
            "status": "available",
            "values": prices,
            "urls": price_urls,
            "min": min(price_values),
            "max": max(price_values),
            "difference": max(price_values) - min(price_values),
            "median": median_price,
            "anomalies": anomalies,
        }

    else:
        price_info = {
            "status": "unavailable",
            "values": {},
            "min": None,
            "max": None,
            "difference": None,
            "median": None,
            "anomalies": [],
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