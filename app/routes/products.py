from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product
from app.schemas import ProductCreate, ProductOut

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductOut, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(Product)
        .filter_by(
            name=payload.name,
            external_id=payload.external_id,
            business_id=payload.business_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Product already exists.")
    product = Product(
        external_id=payload.external_id,
        business_id=payload.business_id,
        product_type=payload.product_type,
        name=payload.name,
        description=payload.description,
    )
    product.attributes = payload.attributes
    db.add(product)
    db.commit()
    db.refresh(product)
    return ProductOut.from_orm_product(product)


@router.get("/{business_id}", response_model=list[ProductOut])
def list_products(business_id: str, db: Session = Depends(get_db)):
    products = db.query(Product).filter_by(business_id=business_id).all()
    return [ProductOut.from_orm_product(p) for p in products]


@router.get("/{business_id}/{external_id}", response_model=ProductOut)
def get_product(business_id: str, external_id: str, db: Session = Depends(get_db)):
    product = (
        db.query(Product)
        .filter_by(external_id=external_id, business_id=business_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return ProductOut.from_orm_product(product)


@router.put("/{business_id}/{external_id}", response_model=ProductOut)
def update_product(
    business_id: str,
    external_id: str,
    payload: ProductCreate,
    db: Session = Depends(get_db),
):
    product = (
        db.query(Product)
        .filter_by(external_id=external_id, business_id=business_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    product.name = payload.name
    product.description = payload.description
    product.product_type = payload.product_type
    product.attributes = payload.attributes
    db.commit()
    db.refresh(product)
    return ProductOut.from_orm_product(product)


@router.delete("/{business_id}/{external_id}", status_code=204)
def delete_product(business_id: str, external_id: str, db: Session = Depends(get_db)):
    product = (
        db.query(Product)
        .filter_by(external_id=external_id, business_id=business_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    db.delete(product)
    db.commit()
