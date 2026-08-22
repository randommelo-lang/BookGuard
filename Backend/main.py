from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from validator import validate_book
from analyzer import analyze_book
from normalization import normalize_listing
from source_detector import detect_source

from sources.bookswagon import scrape as scrape_bookswagon
from sources.amazon import scrape as scrape_amazon
from sources.flipkart import scrape as scrape_flipkart
from sources.generic import scrape as scrape_generic


app = FastAPI(title="BookGuard API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    url: str


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest):
    source = detect_source(request.url)

    if source == "bookswagon":
        data = scrape_bookswagon(request.url)

    elif source == "amazon":
        data = scrape_amazon(request.url)

    elif source == "flipkart":
        data = scrape_flipkart(request.url)

    elif source == "other":
        data = scrape_generic(request.url)

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported source: {source}",
        )


    results = data.get("results", [])

    if not results:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "No book listing was found.",
                "source": source,
            },
        )

    listing = results[0]


    listing = normalize_listing(listing)


    validation = validate_book(listing)

    if not validation["valid"]:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Incomplete book listing data",
                "validation": validation,
            },
        )

    analysis = analyze_book(listing)

    return {
        "status": "success",
        "source": source,
        "data": listing,
        "analysis": analysis,
    }