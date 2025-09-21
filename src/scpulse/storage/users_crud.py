from sqlalchemy.orm import Session
from .models.users import User
from src.scpulse.api.schemas.users import UserCreate
from src.scpulse.core.security import get_password_hash


def create_user(db: Session, user: UserCreate) -> User:
    db_user = User(
        name=user.name,
        email=user.email,
        is_active=True,
        hashed_password=get_password_hash(user.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
