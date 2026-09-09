from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.services.prospect_discovery import (
    ProspectDiscovery,
)

from app.api.prospects import (
    router as prospects_router,
)


app = FastAPI(
    title="ESSEMVEE AI SDR",
    description=(
        "AI-powered sales development platform "
        "for ESSEMVEE Technology Services."
    ),
    version="0.3.0",
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
# REQUEST MODELS
# ============================================================


class DiscoveryRequest(BaseModel):

    query: str = Field(
        min_length=2,
        description="Web search query.",
    )

    count: int = Field(
        default=10,
        ge=1,
        le=20,
        description=(
            "Maximum number of search results."
        ),
    )


# ============================================================
# SERIALIZATION HELPERS
# ============================================================


def serialize_value(value: Any):

    """
    Convert Pydantic models and nested objects into
    JSON-compatible values.
    """

    if hasattr(value, "model_dump"):

        return value.model_dump()

    if isinstance(value, list):

        return [
            serialize_value(item)
            for item in value
        ]

    if isinstance(value, tuple):

        return [
            serialize_value(item)
            for item in value
        ]

    if isinstance(value, dict):

        return {
            key: serialize_value(item)
            for key, item in value.items()
        }

    return value


# ============================================================
# ROOT
# ============================================================


@app.get("/")
def root():

    return {
        "application": "ESSEMVEE AI SDR",
        "message": "SDR API is running.",
        "version": "0.3.0",
        "docs": "/docs",
    }


# ============================================================
# HEALTH
# ============================================================


@app.get("/health")
def health():

    return {
        "status": "ok",
        "application": "ESSEMVEE AI SDR",
        "version": "0.3.0",
    }


# ============================================================
# PROSPECT DISCOVERY
# ============================================================


@app.post("/api/discovery/search")
def discovery_search(
    request: DiscoveryRequest,
):

    """
    Run the existing ESSEMVEE prospect discovery engine.

    The endpoint does not implement a second discovery system.

    It calls the existing ProspectDiscovery service so the API
    and CLI use the same business logic.
    """

    print()

    print(
        "[API] Starting prospect discovery"
    )

    print(
        f"[API] Query: {request.query}"
    )

    print(
        f"[API] Count: {request.count}"
    )

    try:

        discovery = ProspectDiscovery()

        prospects = discovery.discover(
            query=request.query,
            count=request.count,
        )

    except Exception as exc:

        print(
            "[API] Discovery failed: "
            f"{exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

    results = []

    for company, signal in prospects:

        results.append(
            {
                "company": serialize_value(
                    company
                ),

                "signal": serialize_value(
                    signal
                ),
            }
        )

    print()

    print(
        "[API] Discovery completed"
    )

    print(
        f"[API] Qualified prospects: "
        f"{len(results)}"
    )

    return {
        "success": True,

        "query": request.query,

        "requested_count": request.count,

        "qualified_count": len(results),

        "prospects": results,
    }


# ============================================================
# PROSPECT INTELLIGENCE ROUTER
# ============================================================

app.include_router(
    prospects_router
)