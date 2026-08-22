from typing import Optional


def create_book_reference(data: dict, source: str) -> dict:

    return {
        "source": source,
        "book_title": data.get("book_title"),
        "author": data.get("author"),
        "isbn_10": data.get("isbn_10"),
        "isbn_13": data.get("isbn_13"),
        "publisher": data.get("publisher"),
        "edition": data.get("edition"),
        "price": data.get("price"),
        "availability": data.get("availability"),
        "seller_name": data.get("seller_name"),
        "product_url": data.get("product_url"),
    }