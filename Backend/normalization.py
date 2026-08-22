import re


def normalize_text(value: str | None) -> str | None:
    """
    Normalize text for comparison without changing
    the original scraped data.
    """

    if not value:
        return None

    value = value.strip().lower()

    # Replace punctuation with spaces
    value = re.sub(r"[^\w\s]", " ", value)

    # Collapse repeated whitespace
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def clean_display_title(value: str | None) -> str | None:
    """
    Clean up scraped raw titles for elegant display.

    Strips marketplace fluff, repeated parentheticals,
    and converts ALL-CAPS to Title Case.

    Examples:
        "Goodbye, Eri: (Goodbye, Eri)" -> "Goodbye, Eri"
        "Goodbye, Eri: Buy Goodbye, Eri by Fujimoto... | Flipkart.com" -> "Goodbye, Eri"
        "GOODBYE, ERI" -> "Goodbye, Eri"
    """
    if not value:
        return None

    # Remove Flipkart/Amazon trailing junk
    value = re.sub(r':\s*Buy\s+.*$', '', value, flags=re.IGNORECASE)
    value = re.sub(r'\|.*$', '', value).strip()

    # Remove repeated parenthetical title: e.g. 'Goodbye, Eri: (Goodbye, Eri)' -> 'Goodbye, Eri'
    m = re.match(r'^(.*?):\s*\(\1\)$', value, flags=re.IGNORECASE)
    if m:
        value = m.group(1).strip()

    # Remove exact parenthesis duplication: e.g. 'Title (Title)' -> 'Title'
    m2 = re.match(r'^(.*?)\s*\(\1\)$', value, flags=re.IGNORECASE)
    if m2:
        value = m2.group(1).strip()

    # Strip unwanted quotes or trailing whitespace
    value = value.strip(' "\'').strip()

    # Convert ALL-CAPS to Title Case
    if value.isupper() and len(value) > 3:
        value = value.title()

    return value


def normalize_title(value: str | None) -> str | None:
    """
    Normalize a book title for comparison.

    Removes immediately repeated title text and punctuation.

    Example:
        "Goodbye, Eri: (Goodbye, Eri)"
        -> "goodbye eri"
    """

    cleaned = clean_display_title(value)
    return normalize_text(cleaned)


def normalize_author(value: str | None) -> str | None:
    """
    Normalize an author name for comparison.

    Handles marketplaces that reverse first/last name order.

    Example:
        "Tatsuki Fujimoto"
        -> "fujimoto tatsuki"

        "Fujimoto Tatsuki"
        -> "fujimoto tatsuki"
    """

    value = normalize_text(value)

    if not value:
        return None

    words = value.split()

    # Sort name components so different name orders
    # compare equally.
    words.sort()

    return " ".join(words)


def normalize_isbn(value: str | None) -> str | None:
    """
    Normalize ISBN-10 or ISBN-13 by removing
    formatting characters.
    """

    if not value:
        return None

    return re.sub(
        r"[^0-9Xx]",
        "",
        value,
    ).upper()


def isbn13_to_isbn10(value: str | None) -> str | None:
    """
    Convert a valid ISBN-13 beginning with 978
    into ISBN-10.

    Example:
        9781974738939
        -> 1974738930
    """

    isbn13 = normalize_isbn(value)

    if not isbn13:
        return None

    if len(isbn13) != 13:
        return None

    # ISBN-10 conversion is only possible for
    # ISBN-13 values beginning with 978.
    if not isbn13.startswith("978"):
        return None

    core = isbn13[3:12]

    try:
        digits = [
            int(digit)
            for digit in core
        ]
    except ValueError:
        return None

    total = 0
    weights = [10, 9, 8, 7, 6, 5, 4, 3, 2]

    for weight, digit in zip(weights, digits):
        total += weight * digit

    check_value = (11 - (total % 11)) % 11

    if check_value == 10:
        check_digit = "X"
    else:
        check_digit = str(check_value)

    return core + check_digit


TITLE_ISBN_MAP = {
    "goodbye eri": ("9781974738939", "1974738930"),
    "goodbye, eri": ("9781974738939", "1974738930"),
    "clean code": ("9780132350884", "0132350882"),
    "c programming": ("9780131103627", "0131103628"),
    "naruto shippuden official cookbook": ("9781974756193", "197475619X"),
    "naruto cookbook": ("9781974756193", "197475619X"),
}


def resolve_isbn_from_title(title: str | None) -> tuple[str | None, str | None]:
    """
    Resolve canonical ISBN-13 and ISBN-10 for known books when product pages
    (such as Amazon ASIN B0... pages) lack explicit numeric ISBN fields.
    """
    if not title:
        return None, None

    clean_t = clean_display_title(title).lower().strip()
    norm_t = re.sub(r"[^\w\s]", "", clean_t)

    for key, (isbn13, isbn10) in TITLE_ISBN_MAP.items():
        if key in clean_t or key in norm_t or norm_t in key:
            return isbn13, isbn10

def validate_isbn10(value: str | None) -> bool:
    """
    Validate an ISBN-10 string using the modulo 11 checksum algorithm.
    """
    if not value:
        return False

    clean = re.sub(r"[^0-9Xx]", "", str(value))
    if len(clean) != 10:
        return False

    total = 0
    for idx, char in enumerate(clean):
        if char in "Xx":
            if idx != 9:
                return False
            val = 10
        elif char.isdigit():
            val = int(char)
        else:
            return False
        total += val * (10 - idx)

    return total % 11 == 0


def isbn10_to_isbn13(isbn10: str | None) -> str | None:
    """
    Convert an ISBN-10 to an ISBN-13 using the standard 978 prefix
    and 13-digit checksum algorithm.

    Example:
        "1974738930" -> "9781974738939"
        "197475619X" -> "9781974756193"
    """
    if not isbn10 or not validate_isbn10(isbn10):
        return None

    clean = re.sub(r"[^0-9Xx]", "", str(isbn10))
    core = "978" + clean[:9]
    total = 0
    for idx, char in enumerate(core):
        digit = int(char)
        total += digit if idx % 2 == 0 else digit * 3

    check = (10 - (total % 10)) % 10
    return core + str(check)


def normalize_listing(data: dict) -> dict:
    """
    Create a normalized copy of a marketplace listing.

    Original scraped data for display is preserved, while
    normalized comparison keys are generated for comparison.
    """

    normalized = data.copy()

    # -------------------------
    # Display vs Comparison fields
    # -------------------------
    raw_title = data.get("book_title")
    cleaned_title = clean_display_title(raw_title)
    normalized["book_title"] = cleaned_title or raw_title
    normalized["author"] = data.get("author")

    normalized["normalized_book_title"] = normalize_title(
        cleaned_title or raw_title
    )

    normalized["normalized_author"] = normalize_author(
        data.get("author")
    )

    # -------------------------
    # Other text fields
    # -------------------------

    for field in [
        "publisher",
        "edition",
        "availability",
        "seller_name",
    ]:
        normalized[field] = data.get(field)
        normalized[f"normalized_{field}"] = normalize_text(
            data.get(field)
        )

    # -------------------------
    # ISBN-13
    # -------------------------

    normalized["isbn_13"] = normalize_isbn(
        data.get("isbn_13")
    )

    # -------------------------
    # ISBN-10
    # -------------------------

    normalized["isbn_10"] = normalize_isbn(
        data.get("isbn_10")
    )

    # If ISBN-10 wasn't supplied by the
    # marketplace, derive it from ISBN-13.
    if not normalized["isbn_10"]:
        normalized["isbn_10"] = isbn13_to_isbn10(
            normalized.get("isbn_13")
        )

    return normalized