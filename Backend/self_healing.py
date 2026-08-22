import os
import re
import time
import urllib.parse
import httpx

from normalization import (
    normalize_isbn,
    isbn13_to_isbn10,
    isbn10_to_isbn13,
    resolve_isbn_from_title,
    clean_display_title,
    normalize_title,
    normalize_author,
)

from brightdata import (
    BRIGHTDATA_API_KEY,
    scrape_amazon,
    scrape_amazon_product,
    scrape_flipkart,
    search_flipkart,
    search_bookswagon,
    trigger_flipkart_dataset,
    trigger_amazon_product_collector,
)
from live_scraper import (
    scrape_live_amazon,
    scrape_live_flipkart,
    scrape_live_bookswagon,
    extract_isbn,
)


class SelfHealingScraper:
    """
    Autonomous Self-Healing Scraping Engine for BookGuard.

    Continuously monitors scrape quality, detects anti-bot blocks (403, Captcha),
    schema drift, missing ISBNs, or unparsed prices, and automatically escalates
    through multi-tier recovery tactics (Direct Browser -> Bright Data Collector API -> Schema Healing).
    """

    def __init__(self):
        self.api_key_available = bool(BRIGHTDATA_API_KEY)

    def classify_failure(self, raw_data: dict | None, html_content: str | None = None) -> str | None:
        """
        Classify the root cause of a scraping failure.
        """
        if html_content:
            lower_html = html_content.lower()
            if "recaptcha" in lower_html or "captcha" in lower_html:
                return "Anti-Bot Captcha / reCAPTCHA Block Detected"
            if "403 forbidden" in lower_html or "access denied" in lower_html:
                return "HTTP 403 Forbidden Access Block"
            if "filenotfound" in lower_html or "file not found" in lower_html:
                return "Marketplace Listing 404 / File Not Found"

        if not raw_data or not isinstance(raw_data, dict):
            return "Empty or Null Scraper Response"

        missing_fields = []
        if not raw_data.get("book_title"):
            missing_fields.append("book_title")

        price = raw_data.get("price")
        if not price or (isinstance(price, dict) and price.get("value") is None):
            missing_fields.append("price")

        if not raw_data.get("isbn_13") and not raw_data.get("isbn_10"):
            missing_fields.append("isbn")

        if missing_fields:
            return f"Incomplete Schema (Missing: {', '.join(missing_fields)})"

        return None

    def heal_schema(self, listing: dict, original_query: str | None = None) -> tuple[dict, list[str]]:
        """
        Apply intelligent self-healing schema repair on a listing.
        """
        healed = listing.copy()
        repaired_fields = []

        # 1. Title Cleaning & Normalization
        raw_title = healed.get("book_title")
        clean_t = clean_display_title(raw_title)
        if clean_t and clean_t != raw_title:
            healed["book_title"] = clean_t
            repaired_fields.append("book_title (stripped fluff)")

        # 2. ISBN Self-Healing (Derive ISBN-10 <-> ISBN-13 checksums & Title Resolution)
        isbn_13, isbn_10 = extract_isbn(original_query or healed.get("product_url") or "")
        if not healed.get("isbn_13"):
            if isbn_13:
                healed["isbn_13"] = isbn_13
                repaired_fields.append("isbn_13 (extracted from URL)")
            elif healed.get("isbn_10") or isbn_10:
                conv_13 = isbn10_to_isbn13(healed.get("isbn_10") or isbn_10)
                if conv_13:
                    healed["isbn_13"] = conv_13
                    repaired_fields.append("isbn_13 (derived via ISBN-10 checksum)")

        if not healed.get("isbn_10"):
            target_13 = healed.get("isbn_13") or isbn_13
            if target_13:
                conv_10 = isbn13_to_isbn10(target_13)
                if conv_10:
                    healed["isbn_10"] = conv_10
                    repaired_fields.append("isbn_10 (derived via ISBN-13 checksum)")
            elif isbn_10:
                healed["isbn_10"] = isbn_10
                repaired_fields.append("isbn_10 (extracted from URL)")

        if not healed.get("isbn_13") and not healed.get("isbn_10"):
            res_13, res_10 = resolve_isbn_from_title(healed.get("book_title") or raw_title)
            if res_13:
                healed["isbn_13"] = res_13
                healed["isbn_10"] = res_10
                repaired_fields.append("isbn_13 & isbn_10 (resolved via Title-to-ISBN map)")

        # 3. Price Normalization
        price_data = healed.get("price")
        if isinstance(price_data, (int, float)):
            healed["price"] = {"value": float(price_data), "currency": "INR", "symbol": "₹"}
            repaired_fields.append("price (structured object format)")
        elif isinstance(price_data, dict) and price_data.get("value") is not None:
            price_data["value"] = float(price_data["value"])
            price_data["currency"] = price_data.get("currency", "INR")
            price_data["symbol"] = price_data.get("symbol", "₹")

        return healed, repaired_fields

    def heal_scrape(
        self,
        url_or_query: str,
        store: str,
        title: str | None = None,
        author: str | None = None,
    ) -> dict:
        """
        Execute self-healing extraction pipeline.

        Tier 1: Direct Live Scraper (rotating headers)
        Tier 2: Bright Data Collector API (if API Key set & Tier 1 fails)
        Tier 3: Schema Repair & Data Self-Correction
        """
        store_lower = store.lower().strip()
        start_time = time.time()

        tactic_applied = "Direct Browser Scraper"
        failure_cause = None
        healed_flag = False
        repaired_fields = []
        raw_listing = None

        # ----------------------------------------------------
        # Tactic 1: Direct Live Web Scraper
        # ----------------------------------------------------
        try:
            if store_lower == "amazon":
                raw_listing = scrape_live_amazon(url_or_query, title=title, author=author)
            elif store_lower == "flipkart":
                raw_listing = scrape_live_flipkart(url_or_query, title=title, author=author)
            elif store_lower == "bookswagon":
                raw_listing = scrape_live_bookswagon(url_or_query, title=title, author=author)
        except Exception as exc:
            failure_cause = f"Direct Scraper Exception: {str(exc)}"

        failure_cause = self.classify_failure(raw_listing)

        # ----------------------------------------------------
        # Tactic 2: Bright Data Managed Collector API Escalation
        # ----------------------------------------------------
        if failure_cause and self.api_key_available:
            try:
                bright_data_res = None
                if store_lower == "amazon":
                    isbn_13, isbn_10 = extract_isbn(url_or_query)
                    if url_or_query.startswith("http"):
                        bright_data_res = scrape_amazon_product(url_or_query)
                    else:
                        bright_data_res = scrape_amazon(f"https://www.amazon.in/s?k={isbn_13 or isbn_10 or title}")
                elif store_lower == "flipkart":
                    if url_or_query.startswith("http"):
                        bright_data_res = scrape_flipkart(url_or_query)

                if bright_data_res:
                    if isinstance(bright_data_res, list) and bright_data_res:
                        bright_data_res = bright_data_res[0]

                    if isinstance(bright_data_res, dict) and bright_data_res.get("book_title"):
                        raw_listing = bright_data_res
                        tactic_applied = "Bright Data Managed Collector API"
                        healed_flag = True
                        failure_cause = f"Resolved ({failure_cause})"
            except Exception as exc:
                pass

        # ----------------------------------------------------
        # Tactic 3: Smart Schema Repair & Normalization
        # ----------------------------------------------------
        if raw_listing and isinstance(raw_listing, dict):
            healed_listing, fields_fixed = self.heal_schema(raw_listing, original_query=url_or_query)
            if fields_fixed:
                healed_flag = True
                repaired_fields.extend(fields_fixed)

            if healed_flag and not tactic_applied.startswith("Bright Data"):
                tactic_applied = "Smart Schema Repair Engine"

            healing_meta = {
                "healed": healed_flag,
                "status": "success",
                "failure_cause": failure_cause or "None (Clean Scrape)",
                "tactic_applied": tactic_applied,
                "repaired_fields": repaired_fields,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }

            healed_listing["healing_meta"] = healing_meta
            return {
                "source": store_lower,
                "status": "success",
                "results": [healed_listing],
                "healing_meta": healing_meta,
            }

        # Failure Case: Scraper exhausted all self-healing tiers
        healing_meta = {
            "healed": False,
            "status": "error",
            "failure_cause": failure_cause or "Listing not found or website anti-bot block",
            "tactic_applied": "All Tactic Escalations Exhausted",
            "repaired_fields": [],
            "latency_ms": round((time.time() - start_time) * 1000, 2),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        return {
            "source": store_lower,
            "status": "error",
            "message": f"Self-healing scraper could not extract {store} listing.",
            "results": [],
            "healing_meta": healing_meta,
        }


# Global singleton instance
self_healing_scraper = SelfHealingScraper()
heal_scrape = self_healing_scraper.heal_scrape
