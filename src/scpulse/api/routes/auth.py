from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.scpulse.api.schemas.auth import Token
from src.scpulse.storage.postgres import get_session
from src.scpulse.storage.models.users import User
from src.scpulse.core.security import verify_password, create_access_token
from sqlalchemy.future import select

router = APIRouter()


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_session),
) -> Token:
    query = select(User).where(User.email == form_data.username)
    result = db.execute(query)
    user = result.scalars().first()

    if not user or not verify_password(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=400, detail="Incorrect email or password"
        )

    token = create_access_token(data={"sub": user.email})
    return Token(access_token=token, token_type="bearer")
