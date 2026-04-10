"""SQLAlchemy ORM models.

Products use a generic JSON `attributes` column so any product domain
(books, cars, food, movies …) can be represented without schema changes.
"""
import json
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), unique=True, index=True, nullable=False)
    business_id = Column(String(100), index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    interactions = relationship("Interaction", back_populates="user")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), index=True, nullable=False)
    business_id = Column(String(100), index=True, nullable=False)
    product_type = Column(String(100), nullable=False)  # e.g. "book", "car", "meal"
    name = Column(String(500), nullable=False)
    description = Column(Text, default="")
    # Arbitrary domain-specific fields stored as JSON string
    _attributes = Column("attributes", Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)

    interactions = relationship("Interaction", back_populates="product")

    @property
    def attributes(self) -> dict:
        return json.loads(self._attributes or "{}")

    @attributes.setter
    def attributes(self, value: dict):
        self._attributes = json.dumps(value)


class Interaction(Base):
    """Captures any user-product event (view, like, purchase, rating …)."""

    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    business_id = Column(String(100), index=True, nullable=False)
    event_type = Column(String(50), nullable=False)   # view | like | purchase | rate
    score = Column(Float, default=1.0)                # derived weight (set by config)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="interactions")
    product = relationship("Product", back_populates="interactions")


class BusinessConfig(Base):
    """Stores uploaded per-business YAML/JSON config as raw text."""

    __tablename__ = "business_configs"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(String(100), unique=True, index=True, nullable=False)
    config_yaml = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)