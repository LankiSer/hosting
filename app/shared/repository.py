from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import NoResultFound
from typing import TypeVar, Generic, List, Optional, Type
from app.core.db import Base


ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    async def get_by_id(self, session: AsyncSession, id: int) -> Optional[ModelType]:
        """Получить объект по ID"""
        result = await session.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()
    
    async def get_all(self, session: AsyncSession, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Получить все объекты с пагинацией"""
        result = await session.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()
    
    async def create(self, session: AsyncSession, obj_in: dict) -> ModelType:
        """Создать новый объект"""
        db_obj = self.model(**obj_in)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj
    
    async def update(self, session: AsyncSession, db_obj: ModelType, obj_in: dict) -> ModelType:
        """Обновить объект"""
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj
    
    async def delete(self, session: AsyncSession, id: int) -> bool:
        """Удалить объект по ID"""
        result = await session.execute(delete(self.model).where(self.model.id == id))
        await session.commit()
        return result.rowcount > 0 