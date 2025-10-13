from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import (
    ActivationTokenModel,
    UserGroupEnum,
    UserGroupModel,
    UserModel,
    get_db,
)
from schemas import (
    MessageResponseSchema,
    UserRegistrationRequestSchema,
    UserRegistrationResponseSchema,
)

router = APIRouter()


@router.post(
    "register/",
    response_model=UserRegistrationResponseSchema,
    status_code=201,
    responses={
        409: {
            "model": MessageResponseSchema,
            "description": "User already exists",
        },
        500: {
            "model": MessageResponseSchema,
            "description": "Error occured",
        },
    },
)
async def register_user(
    user_data: UserRegistrationRequestSchema,
    db: AsyncSession = Depends(get_db),
):
    try:
        existing_user = await db.scalar(
            select(UserModel).where(UserModel.email == user_data.email),
        )
        if existing_user:
            raise HTTPException(
                status_code=409,
                detail=f"A user with this email {user_data.email} already exists.",
            )

        user_group = await db.scalar(
            select(UserGroupModel).where(UserGroupModel.name == UserGroupEnum.USER),
        )

        user = UserModel.create(
            email=user_data.email,
            raw_password=user_data.password,
            group_id=user_group.id,
        )

        db.add(user)
        await db.flush()

        token = ActivationTokenModel(user_id=user.id)
        db.add(token)
        await db.commit()

        return user

    except HTTPException:
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during user creation.",
        )
