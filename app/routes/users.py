from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter_by(email=payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=409, detail="User already exists.")
    user = User(
        name=payload.name,
        email=payload.email.lower(),
        external_id=payload.external_id,
        business_id=payload.business_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/", response_model=list[UserOut])
def get_user_list(db: Session = Depends(get_db)):
    userList = (
        db.query(User).all()
    )
    if not userList:
        raise HTTPException(status_code=404, detail="User not found.")
    # return [ProductOut.from_orm_product(p) for p in products]
    return [UserOut.model_validate(u) for u in userList]

@router.get("/{business_id}/{external_id}", response_model=UserOut)
def get_user(business_id: str, external_id: str, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter_by(external_id=external_id, business_id=business_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user
