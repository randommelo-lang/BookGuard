def build_search_query(
    book_title: str | None = None,
    author: str | None = None,
    isbn_13: str | None = None,
):
    parts = []

    if book_title:
        parts.append(book_title)

    if author:
        parts.append(author)

    return " ".join(parts)