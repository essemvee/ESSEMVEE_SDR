from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="ESSEMVEE AI SDR",
    description=(
        "AI-powered sales development platform "
        "for ESSEMVEE Technology Services."
    ),
    version="0.1.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "application": "ESSEMVEE AI SDR",
        "version": "0.1.0",
    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "application": "ESSEMVEE AI SDR",
        "message": "SDR API is running.",
        "docs": "/docs",
    }