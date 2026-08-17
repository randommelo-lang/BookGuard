from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from brightdata import scrape_book
from validator import validate_book


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
    data = scrape_book(request.url)

    validation = validate_book(data)

    if not validation["valid"]:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Incomplete book listing data",
                "validation": validation,
            },
        )

    return {
        "status": "success",
        "data": data,
    }