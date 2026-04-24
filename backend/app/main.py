from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import audits, auth, equipment, locations, users

app = FastAPI(
    title="Halo Inventory API",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(locations.router, prefix="/api/v1")
app.include_router(equipment.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(audits.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
