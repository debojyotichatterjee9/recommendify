"""Pydantic request/response schemas."""

from __future__ import annotations

import uuid
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

# ── Users ──────────────────────────────────────────────────────────────────


class UserCreate(BaseModel):
    name: str = Field(..., max_length=255)
    email: str = Field(..., max_length=255)
    external_id: str = Field(..., max_length=255)
    business_id: str = Field(..., max_length=255)


class UserOut(BaseModel):
    id: UUID
    name: str
    email: str
    external_id: str
    business_id: str

    model_config = {"from_attributes": True}


# ── Products ───────────────────────────────────────────────────────────────


class ProductCreate(BaseModel):
    external_id: str = Field(..., max_length=255)
    business_id: str = Field(..., max_length=255)
    product_type: str = Field(..., max_length=100)
    name: str = Field(..., max_length=255)
    description: str = Field(default="", max_length=2000)
    attributes: dict[str, Any] = Field(default_factory=dict)


class ProductOut(BaseModel):
    id: UUID
    external_id: str
    business_id: str
    product_type: str
    name: str
    description: str
    attributes: dict[str, Any]

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_product(cls, p) -> "ProductOut":
        return cls(
            id=p.id,
            external_id=p.external_id,
            business_id=p.business_id,
            product_type=p.product_type,
            name=p.name,
            description=p.description or "",
            attributes=p.attributes,
        )


# ── Interactions ───────────────────────────────────────────────────────────


class InteractionCreate(BaseModel):
    user_external_id: str = Field(..., max_length=255)
    product_external_id: str = Field(..., max_length=255)
    business_id: str = Field(..., max_length=255)
    event_type: str = Field(..., max_length=100, examples=["view", "like", "purchase", "rate"])
    raw_score: float | None = None  # optional explicit score; otherwise config-derived


class InteractionOut(BaseModel):
    id: UUID
    user_id: UUID
    product_id: UUID
    business_id: str
    event_type: str
    score: float

    model_config = {"from_attributes": True}


# ── Recommendations ────────────────────────────────────────────────────────


class RecommendRequest(BaseModel):
    user_external_id: str = Field(..., max_length=255)
    business_id: str = Field(..., max_length=255)
    top_n: int = Field(default=10, ge=1, le=100)
    algorithm: str | None = Field(
        default=None, max_length=50  # override config default: "content" | "collab" | "hybrid"
    )


class RecommendedProduct(BaseModel):
    product_id: UUID
    # user_id: UUID
    product_type: str
    description: str
    external_id: str
    name: str
    score: float
    attributes: dict[str, Any]


class RecommendResponse(BaseModel):
    user_external_id: str
    business_id: str
    algorithm_used: str
    recommendations: list[RecommendedProduct]


# ── Business Config ────────────────────────────────────────────────────────


class ConfigOut(BaseModel):
    business_id: str
    config_yaml: str
