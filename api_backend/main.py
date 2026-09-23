from __future__ import annotations
import os
import sys
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", ".env"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

from api_backend.routers import events, cameras, rois, nlp_and_config

app = FastAPI(
    title="AI Edge Surveillance API",
    version="1.0.0",
    description=(
        "Backend for the AI-Driven Edge Surveillance System. "
        "Separates perception (YOLOv8 + ByteTrack) from explainable event intelligence."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse("/docs")


@app.get("/health")
async def health():
    ok = True
    db_status = "unknown"
    try:
        from api_backend.core.db import db
        db_ok = db.ping(timeout_s=1.0)
        db_status = "ok" if db_ok else "unreachable (degraded)"
        if not db_ok:
            ok = False
    except Exception as e:
        db_status = f"error: {str(e)[:80]}"
        ok = False
    return {
        "status": "healthy" if ok else "degraded",
        "database": db_status,
        "service": "surveillance-api",
    }


api_v1 = FastAPI(title="Surveillance API v1")
api_v1.include_router(events.router)
api_v1.include_router(cameras.router)
api_v1.include_router(rois.router)
api_v1.include_router(nlp_and_config.router)
api_v1.include_router(nlp_and_config.router_config)

app.mount("/api/v1", api_v1)


def main() -> None:
    import uvicorn
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run(
        "api_backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    main()
