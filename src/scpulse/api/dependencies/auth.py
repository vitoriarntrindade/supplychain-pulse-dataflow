import os
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from src.scpulse.storage.models.users import User
from sqlalchemy.ext.asyncio import AsyncSession
from src.scpulse.storage.postgres import get_session
from sqlalchemy.future import select

SECRET_KEY: str = os.getenv("SECRET_KEY", "changeme")
ALGORITHM: str = os.getenv("ALGORITHM", "HS256")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_session),
) -> User:
    credentials_exception = HTTPException(
        status_code=401, detail="Could not validate credentials"
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.email == email))
    user: Optional[User] = result.scalars().first()
    if user is None:
        raise credentials_exception

    return user
