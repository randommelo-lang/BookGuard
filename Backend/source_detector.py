from urllib.parse import urlparse


def detect_source(url: str) -> str:
    """
    Detect the marketplace or website source from a URL.

    Returns:
        "amazon"
        "flipkart"
        "bookswagon"
        "other"
        "unknown"
    """

    if not url:
        return "unknown"

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        hostname = urlparse(url).netloc.lower()

        # Remove www. for easier matching
        hostname = hostname.removeprefix("www.")

        if hostname == "amazon.in" or hostname.endswith(".amazon.in"):
            return "amazon"

        if hostname == "flipkart.com" or hostname.endswith(".flipkart.com"):
            return "flipkart"

        if hostname == "bookswagon.com" or hostname.endswith(".bookswagon.com"):
            return "bookswagon"

        return "other"

    except ValueError:
        return "unknown"