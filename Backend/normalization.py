import re


def normalize_text(value: str | None) -> str | None:
    """
    Normalize text for comparison without changing the original data.
    """

    if not value:
        return None

    value = value.strip().lower()

    value = re.sub(r"[^\w\s]", " ", value)

    value = re.sub(r"\s+", " ", value)

    return value.strip()


def normalize_title(value: str | None) -> str | None:
    """
    Normalize a book title for comparison.

    Also removes an immediately repeated title.

    Example:
        "Goodbye, Eri: (Goodbye, Eri)"
        → "goodbye eri"
    """

    value = normalize_text(value)

    if not value:
        return None

    words = value.split()


    if len(words) % 2 == 0:
        midpoint = len(words) // 2

        first_half = words[:midpoint]
        second_half = words[midpoint:]

        if first_half == second_half:
            value = " ".join(first_half)

    return value


def normalize_isbn(value: str | None) -> str | None:
    """
    Normalize ISBN-10 or ISBN-13 by removing formatting characters.
    """

    if not value:
        return None

    return re.sub(r"[^0-9Xx]", "", value).upper()


def normalize_listing(data: dict) -> dict:
    """
    Create a normalized copy of a marketplace listing.

    Original scraped data is not modified.
    """

    normalized = data.copy()


    normalized["book_title"] = normalize_title(
        data.get("book_title")
    )

    for field in [
        "author",
        "publisher",
        "edition",
        "availability",
        "seller_name",
    ]:
        normalized[field] = normalize_text(data.get(field))

    normalized["isbn_10"] = normalize_isbn(
        data.get("isbn_10")
    )

    normalized["isbn_13"] = normalize_isbn(
        data.get("isbn_13")
    )

    return normalized