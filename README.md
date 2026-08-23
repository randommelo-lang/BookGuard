# BookGuard — Book Authenticity & Price Detector

```text

 ######                        #####                              
 #     #  ####   ####  #    # #     # #    #   ##   #####  #####  
 #     # #    # #    # #   #  #       #    #  #  #  #    # #    # 
 ######  #    # #    # ####   #  #### #    # #    # #    # #    # 
 #     # #    # #    # #  #   #     # #    # ###### #####  #    # 
 #     # #    # #    # #   #  #     # #    # #    # #   #  #    # 
 ######   ####   ####  #    #  #####   ####  #    # #    # #####  
                                                                  
```

> **Verify book listings across Amazon, Flipkart & Bookswagon. Detect counterfeit risks, metadata discrepancies, and price anomalies in seconds.**

Built for **[Into the Scrape-Verse Hackathon](https://www.wemakedevs.org)** by **WeMakeDevs & Bright Data**.

---

## Overview

**BookGuard** is an open-source, automated e-commerce web intelligence and counterfeit risk detection engine. By extracting publicly available book listing data across **Amazon India**, **Flipkart**, and **Bookswagon**, BookGuard identifies counterfeit risks, missing publisher metadata, seller anomalies, and price discrepancies in real time.

---

## Key Features & Highlights

- **Vintage Book & Glassmorphism Theme**: Crafted with an old parchment paper aesthetic (`#f4ecd8`), Times New Roman typography, frosted glass controls.
- **Bright Data Scraper Studio & Self-Healing Engine**: Built with a 3-tier autonomous recovery pipeline for web data extraction:
  1. *Tier 1*: Direct rotating browser scraper.
  2. *Tier 2*: Bright Data Scraper Studio Custom Collector & Web Unlocker API escalation for anti-bot / Captcha handling.
  3. *Tier 3*: Smart Schema Repair & Normalization Engine (derives missing ISBNs via Modulo-11 checksums and canonical title mapping).
- **Risk Assessment & Health Badges**: Displays dynamic `Health-icon.svg` risk meters (**Green**: Low Risk, **Yellow**: Moderate Risk, **Red**: High Risk Counterfeit Warning).
- **Side-by-Side Marketplace Price Matrix**: Direct comparison matrix providing live prices, seller info, and direct product page links (`/book/p/itm?pid={isbn}`) for Amazon, Flipkart, and Bookswagon.

---

## Bright Data Scraper Studio & Custom Web Scraper

BookGuard uses a **Custom Web Scraper created via Bright Data Scraper Studio**.

### Custom Scraper Architecture
- **Target Marketplaces**: Amazon India (`amazon.in`), Flipkart (`flipkart.com`), and Bookswagon (`bookswagon.com`).
- **Scraper Studio Custom Collector**: Custom workflow definitions configured in Bright Data Scraper Studio to target product detail containers, price tags (`_30jeq3`, `a-price-whole`), ISBN fields, and seller metadata.
- **Web Unlocker Integration**: When direct HTTP requests encounter Captchas or anti-bot defenses, the backend automatically escalates requests through the Bright Data Web Unlocker API.

---

## AI Coding Assistant Disclosure

In compliance with hackathon rules, I disclose the use of AI assistance during the project build:

- **AI Assistant Used**: Google DeepMind's **Antigravity AI Agent**.
- **Scope of AI Assistance**:
  - Pair-programming frontend React components (`LoadingState.jsx`, `app.jsx`).
  - Assisting in CSS glassmorphism keyframes and parchment paper styling.
  - Writing Python unit test assertions in `Backend/test_backend.py`.
- **Solo Technical Contribution**: All core architecture, Bright Data Scraper Studio integration, self-healing pipeline algorithms, Modulo-11 ISBN checksum logic, and data verification schemas were independently designed, verified, and implemented by me.

---

## Example Structured Output

Sample JSON output returned by `/api/auto-compare`:

```json
{
  "status": "success",
  "primary_listing": {
    "book_title": "Goodbye, Eri",
    "author": "Tatsuki Fujimoto",
    "isbn_13": "9781974738939",
    "isbn_10": "1974738930",
    "publisher": "VIZ Media",
    "price": {
      "value": 983.0,
      "currency": "INR",
      "symbol": "₹"
    },
    "availability": "In Stock",
    "seller_name": "Amazon Seller",
    "product_url": "https://www.amazon.in/Goodbye-Eri-Tatsuki-Fujimoto/dp/1974738930",
    "store": "Amazon"
  },
  "discovered_listings": [
    {
      "book_title": "Goodbye, Eri",
      "author": "Tatsuki Fujimoto",
      "isbn_13": "9781974738939",
      "isbn_10": "1974738930",
      "price": { "value": 983.0, "currency": "INR", "symbol": "₹" },
      "store": "Amazon",
      "product_url": "https://www.amazon.in/Goodbye-Eri-Tatsuki-Fujimoto/dp/1974738930"
    },
    {
      "book_title": "Goodbye, Eri",
      "author": "Tatsuki Fujimoto",
      "isbn_13": "9781974738939",
      "isbn_10": "1974738930",
      "price": { "value": 160.0, "currency": "INR", "symbol": "₹" },
      "store": "Flipkart",
      "product_url": "https://www.flipkart.com/book/p/itm?pid=9781974738939"
    },
    {
      "book_title": "Goodbye Eri",
      "author": "Tatsuki Fujimoto",
      "isbn_13": "9781974738939",
      "isbn_10": "1974738930",
      "price": { "value": 888.0, "currency": "INR", "symbol": "₹" },
      "store": "Bookswagon",
      "product_url": "https://www.bookswagon.com/book/book/9781974738939"
    }
  ],
  "analysis": {
    "risk_score": 10,
    "risk_level": "low",
    "signals": [
      {
        "type": "identity",
        "status": "good",
        "message": "Official ISBN identifier is present"
      },
      {
        "type": "identity",
        "status": "good",
        "message": "Author information is present"
      }
    ]
  },
  "comparison": {
    "price": {
      "values": {
        "Amazon": 983.0,
        "Flipkart": 160.0,
        "Bookswagon": 888.0
      },
      "anomalies": [
        {
          "source": "Flipkart",
          "severity": "critical",
          "message": "Flipkart price (₹160) is 83% below Amazon average (₹983). High risk of counterfeit reprint."
        }
      ]
    }
  },
  "healing_meta": {
    "healed": true,
    "status": "success",
    "tactic_applied": "Smart Schema Repair Engine",
    "repaired_fields": ["isbn_10 (derived via ISBN-13 checksum)"],
    "latency_ms": 680.45
  }
}
```

---

## Technology Stack

- **Backend**: Python 3.13, FastAPI, Uvicorn, HTTPX, BeautifulSoup4, Modulo-11 Checksum Validation.
- **Frontend**: React 18, Vite, Vanilla CSS Glassmorphism, Times New Roman Typography.
- **Web Data Extraction**: Bright Data Scraper Studio, Custom Web Scraper, Bright Data Web Unlocker API.

---

## Running Locally

### 1. Clone the Repository
```bash
git clone https://github.com/randommelo-lang/BookGuard.git
cd Bookguard
```

### 2. Set Up & Start Backend
```bash
cd Backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
*Backend runs on `http://127.0.0.1:8000`.*

### 3. Set Up & Start Frontend
```bash
cd ../Frontend
npm install
npm run dev
```
*Frontend runs on `http://localhost:5173`.*

### 4. Run Backend Test Suite
```bash
python3 Backend/test_backend.py
```

---

## Code of Conduct & IP Ownership

- **Code of Conduct**: This project adheres strictly to the [WeMakeDevs Code of Conduct](https://www.wemakedevs.org/coc).
- **Intellectual Property**: All IP developed during Into the Scrape-Verse belongs to the project creators.
- **Public Data Compliance**: BookGuard only accesses publicly available e-commerce product listings and does not collect login-protected, paywalled, or government data.

---

*Created for Into the Scrape-Verse Hackathon 2026.*
