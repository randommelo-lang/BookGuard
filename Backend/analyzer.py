from identity import verify_identity

def analyze_book(data: dict) -> dict:
    signals = []
    risk_score = 0

    identity = verify_identity(data)

    # -------------------------
    # Identity signals
    # -------------------------

    if data.get("isbn_13"):
        signals.append({
            "type": "identity",
            "status": "good",
            "message": "ISBN-13 is present",
        })
    else:
        signals.append({
            "type": "identity",
            "status": "warning",
            "message": "ISBN-13 is missing",
        })
        risk_score += 25

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

    availability = data.get("availability", "")

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
    # Price signal
    # -------------------------

    price = data.get("price")

    if price and price.get("value") is not None:
        signals.append({
            "type": "price",
            "status": "good",
            "message": "Price information is available",
        })
    else:
        signals.append({
            "type": "price",
            "status": "warning",
            "message": "Price information is missing",
        })
        risk_score += 25

    # -------------------------
    # Final risk level
    # -------------------------

    risk_score = min(risk_score, 100)

    if risk_score <= 20:
        risk_level = "low"
    elif risk_score <= 50:
        risk_level = "medium"
    else:
        risk_level = "high"

    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "signals": signals,
        "identity": identity,
    }