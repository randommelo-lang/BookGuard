from brightdata import scrape_book


def scrape(url: str) -> dict:
    """
    Generic public book listing scraper.

    Uses the existing Bright Data scraper as the extraction layer.
    """

    return scrape_book(url)