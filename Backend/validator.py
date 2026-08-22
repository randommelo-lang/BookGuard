CORE_REQUIRED_FIELDS = [
    "book_title",
    "product_url",
]

SECONDARY_FIELDS = [
    "author",
    "price",
    "availability",
]


def validate_book(data: dict) -> dict:
    missing_fields = []
    warnings = []

    # Check core fields
    for field in CORE_REQUIRED_FIELDS:
        val = data.get(field)
        if not val:
            missing_fields.append(field)

    # Check ISBN (needs either isbn_13 or isbn_10)
    if not data.get("isbn_13") and not data.get("isbn_10"):
        warnings.append("isbn_13")

    # Check secondary fields as warnings
    for field in SECONDARY_FIELDS:
        val = data.get(field)
        if field == "price":
            if not (isinstance(val, dict) and val.get("value") is not None):
                warnings.append("price")
        elif not val:
            warnings.append(field)

    return {
        "valid": len(missing_fields) == 0,
        "missing_fields": missing_fields,
        "warnings": warnings,
    }