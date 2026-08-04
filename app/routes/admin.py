"""Admin endpoints: upload business configuration YAML."""
from datetime import datetime, timezone

import yaml
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import BusinessConfig
from app.schemas import ConfigOut

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/config/{business_id}", response_model=ConfigOut)
async def upload_config(
    business_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    """Upload a YAML configuration file for a business."""
    content = await file.read()
    try:
        text = content.decode("utf-8")
        yaml.safe_load(text)  # validate YAML
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {exc}")

    row = db.query(BusinessConfig).filter_by(business_id=business_id).first()
    if row:
        row.config_yaml = text
        row.updated_at = datetime.now(timezone.utc)
    else:
        row = BusinessConfig(business_id=business_id, config_yaml=text)
        db.add(row)
    db.commit()
    db.refresh(row)
    return ConfigOut(business_id=row.business_id, config_yaml=row.config_yaml)


@router.get("/config/{business_id}", response_model=ConfigOut)
def get_config(business_id: str, db: Session = Depends(get_db)):
    row = db.query(BusinessConfig).filter_by(business_id=business_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="No config found for this business.")
    return ConfigOut(business_id=row.business_id, config_yaml=row.config_yaml)