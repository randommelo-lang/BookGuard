import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from normalization import isbn13_to_isbn10, normalize_listing
from validator import validate_book
from source_detector import detect_source
from analyzer import analyze_book
from comparison import compare_listings

def test_isbn10_conversion():
    # Kernighan & Ritchie C Programming Language
    isbn10_1 = isbn13_to_isbn10("9780131103627")
    assert isbn10_1 == "0131103628", f"Expected 0131103628, got {isbn10_1}"

    # Goodbye Eri ISBN
    isbn10_2 = isbn13_to_isbn10("9781974738939")
    assert isbn10_2 == "1974738930", f"Expected 1974738930, got {isbn10_2}"
    print("✓ ISBN-10 Checksum Algorithm Test Passed!")

def test_source_detection():
    assert detect_source("amazon.in/dp/B000") == "amazon"
    assert detect_source("https://www.flipkart.com/book/p/123") == "flipkart"
    assert detect_source("bookswagon.com/book/123") == "bookswagon"
    print("✓ Source Detection Test Passed!")

def test_normalization_and_validation():
    sample_listing = {
        "book_title": "The Art of Computer Programming",
        "author": "Donald E. Knuth",
        "isbn_13": "9780201896831",
        "price": {"value": 1499.0, "currency": "INR", "symbol": "₹"},
        "availability": "In Stock",
        "product_url": "https://amazon.in/dp/0201896834",
    }
    
    val = validate_book(sample_listing)
    assert val["valid"] is True, f"Validation failed: {val}"
    
    norm = normalize_listing(sample_listing)
    assert norm["book_title"] == "The Art of Computer Programming"
    assert norm["author"] == "Donald E. Knuth"
    assert norm["isbn_10"] == "0201896834"
    print("✓ Normalization and Validation Test Passed!")

def test_analyzer():
    # Normal price listing
    listing_normal = {
        "book_title": "Clean Code",
        "author": "Robert C. Martin",
        "isbn_13": "9780132350884",
        "price": {"value": 499.0, "currency": "INR", "symbol": "₹"},
        "availability": "In Stock",
        "seller_name": "Tech Books",
        "store": "Amazon",
    }
    analysis_normal = analyze_book(listing_normal)
    assert analysis_normal["risk_level"] == "low"

    # Suspiciously low price listing (e.g. Flipkart Goodbye Eri @ ₹99)
    listing_low_price = {
        "book_title": "Goodbye Eri",
        "author": "Tatsuki Fujimoto",
        "isbn_13": "9781974738939",
        "price": {"value": 99.0, "currency": "INR", "symbol": "₹"},
        "availability": "In Stock",
        "seller_name": "Discount Books",
        "store": "Flipkart",
    }
    analysis_low = analyze_book(listing_low_price)
    assert analysis_low["risk_level"] == "high", f"Expected high risk for ₹99 listing, got {analysis_low['risk_level']}"
    print("✓ Low Price High Risk Detection Test Passed!")

def test_self_healing():
    from self_healing import SelfHealingScraper
    from live_scraper import extract_isbn
    healer = SelfHealingScraper()

    # Test URL query param filtering (e.g. qid=1787399784 must NOT be mistaken for an ISBN)
    asin_url = "https://www.amazon.in/Goodbye-Eri-New-Pages1-Team/dp/B0FGXH7RWV?qid=1787399784"
    isbn13_found, isbn10_found = extract_isbn(asin_url)
    assert isbn13_found is None, f"Expected None for isbn_13 on ASIN URL, got {isbn13_found}"
    assert isbn10_found is None, f"Expected None for isbn_10 on ASIN URL, got {isbn10_found}"
    print("✓ URL Query Parameter (qid) Filtering Test Passed!")

    # Test failure classification
    assert healer.classify_failure(None) == "Empty or Null Scraper Response"
    assert healer.classify_failure({}, html_content="<html>reCAPTCHA</html>") == "Anti-Bot Captcha / reCAPTCHA Block Detected"

    # Test schema repair (derive ISBN-10 from ISBN-13 & clean title fluff)
    raw_unhealed = {
        "book_title": "Goodbye, Eri: (Goodbye, Eri)",
        "isbn_13": "9781974738939",
        "price": 888.0,
        "store": "Bookswagon"
    }

    healed_dict, repaired = healer.heal_schema(raw_unhealed)
    assert healed_dict["book_title"] == "Goodbye, Eri"
    assert healed_dict["isbn_10"] == "1974738930"
    assert healed_dict["price"]["value"] == 888.0
    assert "isbn_10 (derived via ISBN-13 checksum)" in repaired
    print("✓ Self-Healing Engine Unit Test Passed!")

if __name__ == "__main__":
    test_isbn10_conversion()
    test_source_detection()
    test_normalization_and_validation()
    test_analyzer()
    test_self_healing()
    print("\nALL BACKEND UNIT TESTS PASSED SUCCESSFULLY!")
