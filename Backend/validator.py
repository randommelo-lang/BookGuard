REQUIRED_FIELDS = [
    "book_title",
    "author",
    "isbn_13",
    "price",
    "availability",
    "product_url",
]


def validate_book(data: dict) -> dict:
    missing_fields = [
        field
        for field in REQUIRED_FIELDS
        if not data.get(field)
    ]

    return {
        "valid": len(missing_fields) == 0,
        "missing_fields": missing_fields,
        "warnings": [],
    }