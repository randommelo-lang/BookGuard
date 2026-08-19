def verify_identity(data: dict) -> dict:
    checks = []

    if data.get("isbn_13"):
        checks.append({
            "field": "isbn_13",
            "status": "available",
            "message": "ISBN-13 is available for verification",
        })
    else:
        checks.append({
            "field": "isbn_13",
            "status": "missing",
            "message": "ISBN-13 is unavailable",
        })

    if data.get("book_title"):
        checks.append({
            "field": "book_title",
            "status": "available",
            "message": "Book title is available for verification",
        })

    if data.get("author"):
        checks.append({
            "field": "author",
            "status": "available",
            "message": "Author is available for verification",
        })

    if data.get("publisher"):
        checks.append({
            "field": "publisher",
            "status": "available",
            "message": "Publisher is available for verification",
        })

    return {
        "status": "pending",
        "message": "Identity verification requires an external book reference.",
        "checks": checks,
    }