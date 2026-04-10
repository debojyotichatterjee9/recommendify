"""Recommendation Service — FastAPI entry point."""
from fastapi import FastAPI

from app.database import Base, engine
# from app.routes import admin, interactions, products, recommendations, users

# Create all tables on startup (SQLite auto-creates the file)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Recommendation Service",
    description=(
        "A product-agnostic recommendation engine supporting any business domain. "
        "Configure per-business algorithm weights and interaction scoring via YAML."
    ),
    version="1.0.0",
)

# app.include_router(users.router)
# app.include_router(products.router)
# app.include_router(interactions.router)
# app.include_router(recommendations.router)
# app.include_router(admin.router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "Recommendation Service"}