import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.loader import load_config
from app.database import get_db
from app.models import BusinessConfig, Interaction, Product, User
from app.recommender.engine import get_recommendations
from app.schemas import RecommendedProduct, RecommendRequest, RecommendResponse

router = APIRouter(prefix="/recommend", tags=["Recommendations"])


@router.post("/", response_model=RecommendResponse)
def recommend(payload: RecommendRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(
        external_id=payload.user_external_id, business_id=payload.business_id
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Load config
    cfg_row = db.query(BusinessConfig).filter_by(business_id=payload.business_id).first()
    config = load_config(cfg_row.config_yaml if cfg_row else None)

    # Build products DataFrame
    products = db.query(Product).filter_by(business_id=payload.business_id).all()
    if not products:
        return RecommendResponse(
            user_external_id=payload.user_external_id,
            business_id=payload.business_id,
            algorithm_used="none",
            recommendations=[],
        )

    products_df = pd.DataFrame([
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "product_type": p.product_type,
            "attributes": p.attributes,
        }
        for p in products
    ])

    # Build interactions DataFrame
    interactions = db.query(Interaction).filter_by(business_id=payload.business_id).all()
    interactions_df = pd.DataFrame([
        {"user_id": i.user_id, "product_id": i.product_id, "score": i.score}
        for i in interactions
    ]) if interactions else pd.DataFrame(columns=["user_id", "product_id", "score"])

    top_ids, algo_used = get_recommendations(
        target_user_id=user.id,
        products_df=products_df,
        interactions_df=interactions_df,
        config=config,
        top_n=payload.top_n,
        algorithm_override=payload.algorithm,
    )

    # Fetch ordered product details
    id_to_product = {p.id: p for p in products}

    # Build score map for response
    scores_map: dict[int, float] = {}
    if top_ids:
        # Re-run to get raw scores for display (simplified: equal rank-based)
        for rank, pid in enumerate(top_ids):
            scores_map[pid] = round(1.0 - rank / max(len(top_ids), 1), 4)

    recommendations = [
        RecommendedProduct(
            product_id=pid,
            # user_id=id_to_product[pid].user_id,
            external_id=id_to_product[pid].external_id,
            name=id_to_product[pid].name,
            product_type=id_to_product[pid].product_type,
            score=scores_map.get(pid, 0.0),
            description=id_to_product[pid].description,
            attributes=id_to_product[pid].attributes,
        )
        for pid in top_ids
        if pid in id_to_product
    ]

    return RecommendResponse(
        user_external_id=payload.user_external_id,
        business_id=payload.business_id,
        algorithm_used=algo_used,
        recommendations=recommendations,
    )