from fastapi import APIRouter, Depends, HTTPException
from src.scpulse.api.schemas.users import UserOut, UserCreate
from src.scpulse.api.dependencies.auth import get_current_user
from src.scpulse.storage.models.users import User
from src.scpulse.storage.postgres import get_session
from src.scpulse.storage.users_crud import create_user

from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/me", response_model=UserOut)
def read_own_profile(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/users/", response_model=UserOut)
def create_user_route(
    user: UserCreate, db: Session = Depends(get_session)
) -> User:
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email já registrado")
    return create_user(db, user)
