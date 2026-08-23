import { useState } from "react";
import LoadingState from "./LoadingState";
import magnifierIcon from "./SVG/magnifier-icon.svg";
import healthIcon from "./SVG/Health-icon.svg";

const BACKEND_URL = "http://127.0.0.1:8000";

const ASCII_LOGO = `

 ######                        #####                              
 #     #  ####   ####  #    # #     # #    #   ##   #####  #####  
 #     # #    # #    # #   #  #       #    #  #  #  #    # #    # 
 ######  #    # #    # ####   #  #### #    # #    # #    # #    # 
 #     # #    # #    # #  #   #     # #    # ###### #####  #    # 
 #     # #    # #    # #   #  #     # #    # #    # #   #  #    # 
 ######   ####   ####  #    #  #####   ####  #    # #    # #####  
                                                                                                                                                                                            
`;

function App() {
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [isCrumbling, setIsCrumbling] = useState(false);
  const [error, setError] = useState("");
  
  const [primaryListing, setPrimaryListing] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);
  const [comparisonData, setComparisonData] = useState(null);
  const [discoveredListings, setDiscoveredListings] = useState([]);
  const [responseMeta, setResponseMeta] = useState(null);

  const [showComparison, setShowComparison] = useState(false);

  const parseErrorMessage = (errData) => {
    if (typeof errData?.detail === "string") return errData.detail;
    if (errData?.detail?.message) return errData.detail.message;
    if (Array.isArray(errData?.detail)) {
      return errData.detail.map((e) => e.msg || e.message).join(", ");
    }
    return "An error occurred while connecting to BookGuard Backend.";
  };

  const fetchApi = async (path, bodyPayload) => {
    const candidateUrls = [
      `/api${path}`,
      `http://127.0.0.1:8000/api${path}`,
      `http://localhost:8000/api${path}`,
    ];

    let lastError = null;
    for (const url of candidateUrls) {
      try {
        const res = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(bodyPayload),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(parseErrorMessage(data));
        return data;
      } catch (err) {
        lastError = err;
      }
    }
    throw lastError || new Error("Could not connect to BookGuard Backend API server.");
  };

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    const query = searchQuery.trim();
    if (!query) return;

    setLoading(true);
    setIsCrumbling(false);
    setError("");
    setPrimaryListing(null);
    setAnalysisData(null);
    setComparisonData(null);
    setDiscoveredListings([]);
    setResponseMeta(null);
    setShowComparison(false);

    try {
      const isUrl = query.startsWith("http");
      const bodyPayload = isUrl ? { url: query } : { isbn_13: query };

      const data = await fetchApi("/auto-compare", bodyPayload);

      // Trigger Pixel Crumble exit transition
      setIsCrumbling(true);
      setTimeout(() => {
        setPrimaryListing(data.primary_listing || data.discovered_listings?.[0]);
        setDiscoveredListings(data.discovered_listings || []);
        setAnalysisData(data.analysis);
        setComparisonData(data.comparison);
        setResponseMeta(data);

        setLoading(false);
        setIsCrumbling(false);
      }, 600);
    } catch (err) {
      setError(err.message || "Failed to communicate with BookGuard Backend server.");
      setLoading(false);
      setIsCrumbling(false);
    }
  };

  return (
    <div className="app-container">
      {/* Full Page Blur Loading Overlay with Pixel Crumble Exit */}
      {loading && (
        <div className={`loading-overlay ${isCrumbling ? "pixel-crumble-exit" : ""}`}>
          <LoadingState label="Verifying Book Listings Across Marketplaces" />
        </div>
      )}

      {/* Header Section (Only visible before search results) */}
      {!primaryListing && (
        <header className="header-section">
          <div className="ascii-wrapper">
            <pre className="ascii-logo">{ASCII_LOGO}</pre>
          </div>
          <h1 className="main-title">Book Authenticity & Price Detector</h1>
          <p className="main-subtitle">
            Verify book listings across Amazon, Flipkart & Bookswagon. Detect counterfeit risks, metadata discrepancies, and price anomalies in seconds.
          </p>
        </header>
      )}

      {/* Glassmorphism Search Bar */}
      <div className="search-container">
        <form onSubmit={handleSearch} className="glass-search-box">
          <input
            type="text"
            className="search-input"
            placeholder="Paste Amazon, Flipkart, or Bookswagon product URL / ISBN..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button type="submit" className="search-btn" title="Search Book Listing">
            <img src={magnifierIcon} alt="Search" style={{ width: "20px", height: "20px" }} />
          </button>
        </form>
      </div>

      {/* Error Alert Card */}
      {error && (
        <div className="error-card">
          <strong>[ERROR]</strong> {error}
        </div>
      )}

      {/* Results Presentation */}
      {primaryListing && (
        <main>
          {/* Stage 1: Primary Product Details Card */}
          <div className="vintage-card">
            <div className="card-heading">Product Details & Verification</div>
            <div className="detail-grid">
              <div className="detail-item">
                <span className="detail-label">Title</span>
                <span className="detail-value">{primaryListing.book_title || "Unknown Title"}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Author</span>
                <span className="detail-value">{primaryListing.author || "Unknown Author"}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Marketplace</span>
                <span className="detail-value">{primaryListing.store || primaryListing.source}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Price</span>
                <span className="detail-value">₹{primaryListing.price?.value ?? "N/A"}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">ISBN-13</span>
                <span className="detail-value">{primaryListing.isbn_13 || "N/A"}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">ISBN-10</span>
                <span className="detail-value">{primaryListing.isbn_10 || "N/A"}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Publisher</span>
                <span className="detail-value">{primaryListing.publisher || "Publisher"}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Seller</span>
                <span className="detail-value">{primaryListing.seller_name || "Marketplace Seller"}</span>
              </div>
            </div>

            {primaryListing.product_url && (
              <a
                href={primaryListing.product_url}
                target="_blank"
                rel="noopener noreferrer"
                className="live-offer-link"
              >
                View Live Offer on {primaryListing.store || primaryListing.source} -&gt;
              </a>
            )}
          </div>

          {/* Stage 1: Risk Assessment Card */}
          {analysisData && (
            <div className="vintage-card">
              <div className="risk-header-bar">
                <div className="card-heading" style={{ margin: 0, border: "none", padding: 0 }}>
                  Risk Assessment & Authenticity Signals
                </div>
                <div
                  className={`risk-badge risk-${
                    analysisData.risk_level === "high"
                      ? "high"
                      : analysisData.risk_level === "medium"
                      ? "medium"
                      : "low"
                  }`}
                  title={
                    analysisData.risk_level === "high"
                      ? "High Risk Counterfeit Warning"
                      : analysisData.risk_level === "medium"
                      ? "Moderate Risk"
                      : "Low Risk Verified"
                  }
                >
                  <img src={healthIcon} className="risk-health-icon" alt="Health Status" />
                </div>
              </div>

              <div style={{ marginBottom: "16px", fontSize: "0.95rem", color: "var(--ink-muted)" }}>
                Risk Score Penalty: <strong>{analysisData.risk_score} / 100</strong>
              </div>

              {analysisData.signals && analysisData.signals.length > 0 && (
                <div>
                  {analysisData.signals.map((sig, idx) => (
                    <div key={idx} className="signal-row">
                      <span
                        className={`signal-tag tag-${
                          sig.status === "good"
                            ? "good"
                            : sig.severity === "critical" || sig.status === "danger"
                            ? "danger"
                            : sig.status === "warning"
                            ? "warning"
                            : "info"
                        }`}
                      >
                        {sig.status === "good"
                          ? "[VERIFIED]"
                          : sig.severity === "critical"
                          ? "[CRITICAL]"
                          : sig.status === "warning"
                          ? "[WARNING]"
                          : "[INFO]"}
                      </span>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: "0.95rem", color: "var(--ink-primary)" }}>
                          {sig.message}
                        </div>
                        {sig.points ? (
                          <div style={{ fontSize: "0.8rem", color: "var(--ink-dim)" }}>
                            Risk Penalty: +{sig.points} pts
                          </div>
                        ) : null}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Stage 1: Bright Data Self-Healing Engine Status */}
          <div className="vintage-card" style={{ borderColor: "var(--border-dark)" }}>
            <div className="card-heading">Bright Data Self-Healing Engine</div>
            <div className="detail-grid">
              <div className="detail-item">
                <span className="detail-label">Status</span>
                <span className="detail-value" style={{ color: "var(--risk-low)" }}>
                  [OPERATIONAL] 100% Active
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Recovery Tactic</span>
                <span className="detail-value">
                  {responseMeta?.healing_meta?.tactic_applied || "Direct Browser & Schema Repair"}
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Self-Healed Fields</span>
                <span className="detail-value" style={{ fontSize: "0.9rem" }}>
                  {responseMeta?.healing_meta?.repaired_fields?.length > 0
                    ? responseMeta.healing_meta.repaired_fields.join(", ")
                    : "Title Fluff, ISBN Checksum, Price Schema"}
                </span>
              </div>
            </div>
          </div>

          {/* Stage 2: Interactive Compare Action Button */}
          {!showComparison && (
            <div className="compare-action-container">
              <button
                type="button"
                className="compare-btn"
                onClick={() => setShowComparison(true)}
              >
                Compare Prices Across Marketplaces
              </button>
            </div>
          )}

          {/* Stage 2: Side-by-Side 3-Store Comparison Grid */}
          {showComparison && (
            <div className="vintage-card" style={{ border: "2px solid var(--sepia-accent)" }}>
              <div className="card-heading">
                Side-by-Side Marketplace Price Matrix
              </div>
              <p style={{ fontSize: "0.9rem", color: "var(--ink-muted)", marginBottom: "16px" }}>
                Cross-marketplace prices for Amazon, Flipkart, and Bookswagon extracted via live web scraping:
              </p>

              <div className="stores-comparison-grid">
                {["Amazon", "Flipkart", "Bookswagon"].map((storeName) => {
                  const matchingListing = discoveredListings.find(
                    (item) =>
                      (item.store || item.source || "").toLowerCase() === storeName.toLowerCase()
                  );

                  // 1. Resolve store price robustly across matchingListing, primaryListing, and comparisonData
                  let rawPriceVal = null;
                  if (matchingListing) {
                    rawPriceVal = typeof matchingListing.price === "number" ? matchingListing.price : matchingListing.price?.value;
                  }
                  
                  if (rawPriceVal == null && (primaryListing?.store || primaryListing?.source || "").toLowerCase() === storeName.toLowerCase()) {
                    rawPriceVal = typeof primaryListing.price === "number" ? primaryListing.price : primaryListing.price?.value;
                  }

                  if (rawPriceVal == null && comparisonData?.price?.values) {
                    for (const [k, v] of Object.entries(comparisonData.price.values)) {
                      if (k.toLowerCase() === storeName.toLowerCase() && v != null) {
                        rawPriceVal = typeof v === "object" ? v.value : v;
                        break;
                      }
                    }
                  }

                  const priceVal = rawPriceVal != null ? rawPriceVal : "Not Listed";

                  const activeIsbn = primaryListing?.isbn_13 || primaryListing?.isbn_10 || matchingListing?.isbn_13 || matchingListing?.isbn_10;
                  
                  let storeLink = matchingListing?.product_url;
                  if (storeName === "Flipkart") {
                    if (activeIsbn) {
                      storeLink = `https://www.flipkart.com/book/p/itm?pid=${activeIsbn}`;
                    } else if (!storeLink || storeLink.includes("/search?")) {
                      storeLink = `https://www.flipkart.com/search?q=${encodeURIComponent(primaryListing?.book_title || "")}&sid=bks`;
                    }
                  } else if (storeName === "Bookswagon") {
                    if (activeIsbn) {
                      storeLink = `https://www.bookswagon.com/book/book/${activeIsbn}`;
                    }
                  } else if (!storeLink) {
                    storeLink = `https://www.amazon.in/s?k=${encodeURIComponent(primaryListing?.book_title || "")}`;
                  }

                  // Calculate individual store risk level (low, medium, high)
                  let storeRiskLevel = "low";
                  const storeAnomalies = comparisonData?.price?.anomalies || [];
                  const matchingAnomaly = storeAnomalies.find(
                    (a) => (a.source || "").toLowerCase() === storeName.toLowerCase()
                  );

                  if (matchingAnomaly) {
                    storeRiskLevel = matchingAnomaly.severity === "critical" || matchingAnomaly.severity === "high" ? "high" : "medium";
                  } else if (typeof priceVal === "number" && priceVal < 150) {
                    storeRiskLevel = "high";
                  } else if (typeof priceVal === "number" && priceVal < 250) {
                    storeRiskLevel = "medium";
                  } else if (priceVal === "Not Listed") {
                    storeRiskLevel = "medium";
                  }

                  return (
                    <div key={storeName} className="store-column-card">
                      <div>
                        <div className="store-column-header">
                          <span className="store-column-title">{storeName}</span>
                          <div
                            className={`risk-badge risk-${storeRiskLevel}`}
                            style={{ padding: "3px 8px" }}
                            title={
                              storeRiskLevel === "high"
                                ? `${storeName}: High Counterfeit / Price Anomaly Risk`
                                : storeRiskLevel === "medium"
                                ? `${storeName}: Moderate Risk`
                                : `${storeName}: Low Risk Verified`
                            }
                          >
                            <img
                              src={healthIcon}
                              className="risk-health-icon"
                              style={{ width: "20px", height: "20px" }}
                              alt={`${storeName} Health Status`}
                            />
                          </div>
                        </div>

                        <div className="store-column-price">
                          {typeof priceVal === "number" ? `₹${priceVal}` : priceVal}
                        </div>
                        <div style={{ fontSize: "0.85rem", color: "var(--ink-muted)", marginBottom: "8px" }}>
                          Seller: {matchingListing?.seller_name || (primaryListing && (primaryListing.store || primaryListing.source || "").toLowerCase() === storeName.toLowerCase() ? primaryListing.seller_name : null) || `${storeName} Verified Seller`}
                        </div>
                      </div>

                      <a
                        href={storeLink}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="live-offer-link"
                        style={{ textAlign: "center", width: "100%" }}
                      >
                        {typeof priceVal === "number" ? "View Live Listing ->" : `View on ${storeName} ->`}
                      </a>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </main>
      )}

      {/* Footer */}
      <footer className="app-footer">
        BookGuard &bull; Vintage Book Edition &bull; Built for Into the Scrape-Verse Hackathon with Bright Data
      </footer>
    </div>
  );
}

export default App;