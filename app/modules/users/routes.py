from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.auth.models import AuthUsers
from app.modules.auth.routes import get_current_user
from app.modules.users.schemas import UserProfileResponse, UserProfileUpdate

router = APIRouter()


@router.get("/users/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: AuthUsers = Depends(get_current_user),
):
    """Возвращает сведения о текущем пользователе."""
    return UserProfileResponse.model_validate(current_user, from_attributes=True)


@router.patch("/users/me", response_model=UserProfileResponse)
async def update_my_profile(
    user_update: UserProfileUpdate,
    current_user: AuthUsers = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Обновляет основные данные профиля."""

    updated = False

    for field in ("first_name", "last_name", "phone"):
        value = getattr(user_update, field)
        if value is not None:
            setattr(current_user, field, value)
            updated = True

    if not updated:
        return UserProfileResponse.model_validate(current_user, from_attributes=True)

    await db.commit()
    await db.refresh(current_user)

    return UserProfileResponse.model_validate(current_user, from_attributes=True)


@router.get("/users/{user_id}", response_model=UserProfileResponse)
async def get_user_by_id(
    user_id: int,
    current_user: AuthUsers = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Возвращает данные пользователя. Доступно только владельцу записи."""

    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    result = await db.execute(select(AuthUsers).where(AuthUsers.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    return UserProfileResponse.model_validate(user, from_attributes=True)