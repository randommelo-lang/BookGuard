from identity import verify_identity


def analyze_book(
    data: dict,
    comparison: dict | None = None,
) -> dict:
    """
    Analyze a single marketplace listing.

    Optional comparison data can add cross-marketplace
    risk signals.
    """

    signals = []
    risk_score = 0

    # -------------------------
    # Identity signals
    # -------------------------

    if data.get("isbn_13") or data.get("isbn_10"):
        signals.append({
            "type": "identity",
            "status": "good",
            "message": "Official ISBN identifier is present",
        })
    else:
        signals.append({
            "type": "identity",
            "status": "warning",
            "severity": "critical",
            "points": 50,
            "message": "Official ISBN identifier is missing. High risk of unverified or counterfeit listing.",
        })
        risk_score += 50

    if data.get("author"):
        signals.append({
            "type": "identity",
            "status": "good",
            "message": "Author information is present",
        })
    else:
        signals.append({
            "type": "identity",
            "status": "warning",
            "message": "Author information is missing",
        })
        risk_score += 15

    if data.get("publisher"):
        signals.append({
            "type": "identity",
            "status": "good",
            "message": "Publisher information is present",
        })
    else:
        signals.append({
            "type": "identity",
            "status": "warning",
            "message": "Publisher information is missing",
        })
        risk_score += 15

    # -------------------------
    # Listing signals
    # -------------------------

    availability = str(data.get("availability") or "")

    if "international edition" in availability.lower():
        signals.append({
            "type": "edition",
            "status": "info",
            "message": "Listing is marked as an International Edition",
        })

    if data.get("seller_name"):
        signals.append({
            "type": "seller",
            "status": "good",
            "message": "Seller information is available",
        })
    else:
        signals.append({
            "type": "seller",
            "status": "warning",
            "message": "Seller information is missing",
        })
        risk_score += 20

    # -------------------------
    # Identity verification
    # -------------------------
    try:
        identity_res = verify_identity(data)
        for check in identity_res.get("checks", []):
            if check.get("status") == "available" and check.get("field") not in {"isbn_13", "author", "publisher"}:
                signals.append({
                    "type": "identity_check",
                    "status": "good",
                    "message": check.get("message"),
                })
    except Exception:
        pass

    # -------------------------
    # Price signal
    # -------------------------

    price = data.get("price")

    if isinstance(price, dict) and price.get("value") is not None:
        val = float(price.get("value"))
        if val < 150:
            signals.append({
                "type": "price_anomaly",
                "status": "warning",
                "severity": "critical",
                "points": 45,
                "message": f"Listing price (₹{val}) is suspiciously low (under ₹150). High risk of counterfeit print.",
            })
            risk_score += 45
        elif val < 250:
            signals.append({
                "type": "price_anomaly",
                "status": "warning",
                "severity": "high",
                "points": 25,
                "message": f"Listing price (₹{val}) is unusually low (under ₹250). Potential reprint risk.",
            })
            risk_score += 25
        else:
            signals.append({
                "type": "price",
                "status": "good",
                "message": f"Price information is available (₹{val})",
            })
    else:
        signals.append({
            "type": "price",
            "status": "warning",
            "message": "Price information is missing",
        })
        risk_score += 25

    # =====================================================
    # Cross-marketplace comparison signals
    # =====================================================

    if comparison:
        price_comparison = comparison.get("price", {})

        anomalies = price_comparison.get(
            "anomalies",
            [],
        )

        current_source = str(data.get("store") or data.get("source") or "")

        for anomaly in anomalies:

            anomaly_source = str(anomaly.get("source") or "")

            # Only apply the anomaly to the listing
            # that actually has the suspicious price.
            if (
                current_source
                and anomaly_source
                and current_source.lower()
                != anomaly_source.lower()
            ):
                continue

            severity = anomaly.get(
                "severity",
                "medium",
            )

            # comparison.py is responsible for deciding
            # how serious the price anomaly is.
            #
            # Examples:
            #   medium  -> 15
            #   high    -> 30 or 45
            #   critical -> 55
            points = anomaly.get(
                "points",
                0,
            )

            # Safety fallback for older comparison results
            # that don't contain "points".
            if points <= 0:
                if severity == "critical":
                    points = 55

                elif severity == "high":
                    points = 30

                elif severity == "medium":
                    points = 15

                else:
                    points = 5

            risk_score += points

            percentage = anomaly.get(
                "percentage_below_median"
            )

            if percentage is not None:
                message = (
                    f"Listing price is "
                    f"{percentage:.2f}% below the "
                    "comparable marketplace median."
                )
            else:
                message = (
                    "Listing price is significantly "
                    "below comparable marketplace prices."
                )

            signals.append({
                "type": "price_anomaly",
                "status": "warning",
                "severity": severity,
                "points": points,
                "message": message,
            })

        # -------------------------
        # Metadata disagreements
        # -------------------------

        differences = comparison.get(
            "differences",
            [],
        )

        for difference in differences:

            field = difference.get("field")

            # Author order has already been normalized,
            # so an author disagreement here is meaningful.
            risk_points = {
                "isbn_10": 20,
                "isbn_13": 40,
                "book_title": 25,
                "author": 10,
                "publisher": 20,
                "edition": 10,
            }

            points = risk_points.get(
                field,
                5,
            )

            risk_score += points

            signals.append({
                "type": "metadata_disagreement",
                "status": "warning",
                "field": field,
                "points": points,
                "message": (
                    f"{field.replace('_', ' ').title()} "
                    "differs across marketplace listings."
                ),
            })

    # -------------------------
    # Final risk score
    # -------------------------

    risk_score = min(
        risk_score,
        100,
    )

    # -------------------------
    # Final risk level
    # -------------------------

    if risk_score <= 20:
        risk_level = "low"

    elif risk_score <= 40:
        risk_level = "medium"

    else:
        risk_level = "high"

    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "signals": signals,
    }