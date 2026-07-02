from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.loader import get_interaction_score, load_config
from app.database import get_db
from app.models import BusinessConfig, Interaction, Product, User
from app.schemas import InteractionCreate, InteractionOut

router = APIRouter(prefix="/interactions", tags=["Interactions"])


def _resolve_config(business_id: str, db: Session) -> dict:
    row = db.query(BusinessConfig).filter_by(business_id=business_id).first()
    return load_config(row.config_yaml if row else None)


@router.post("/", response_model=InteractionOut, status_code=201)
def log_interaction(payload: InteractionCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(
        external_id=payload.user_external_id, business_id=payload.business_id
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    product = db.query(Product).filter_by(
        external_id=payload.product_external_id, business_id=payload.business_id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    config = _resolve_config(payload.business_id, db)
    score = payload.raw_score if payload.raw_score is not None else get_interaction_score(
        payload.event_type, config
    )

    interaction = Interaction(
        user_id=user.id,
        product_id=product.id,
        business_id=payload.business_id,
        event_type=payload.event_type,
        score=score,
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction