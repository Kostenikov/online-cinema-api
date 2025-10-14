from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from config import get_jwt_auth_manager
from database import UserGroupEnum, UserModel, get_db
from database.models.accounts import BlacklistedTokenModel
from exceptions import BaseSecurityError
from security.interfaces import JWTAuthManagerInterface


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
    db: AsyncSession = Depends(get_db),
) -> UserModel:

    stmt = select(BlacklistedTokenModel).filter_by(token=token)
    result = await db.execute(stmt)
    blacklisted_token = result.scalars().first()

    if blacklisted_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt_manager.decode_access_token(token)
        token_user_id = payload.get("user_id")
    except BaseSecurityError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    user = await db.scalar(
        select(UserModel).where(UserModel.id == token_user_id).options(joinedload(UserModel.group)),
    )

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or not active",
        )

    return user


async def require_admin(
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> UserModel:
    if current_user.group.name != UserGroupEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    return current_user


async def require_moderator(
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> UserModel:
    if current_user.group.name not in [UserGroupEnum.ADMIN, UserGroupEnum.MODERATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or moderator role required",
        )

    return current_user


async def require_user(
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> UserModel:
    return current_user
