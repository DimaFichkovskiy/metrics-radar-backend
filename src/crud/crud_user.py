from typing import Optional, List, Union
from sqlalchemy import select
from fastapi import HTTPException, Depends

from src.database import AsyncSession, get_db_session
from src import models, security, schemas


class UserCRUD:

    def __init__(self, db: AsyncSession = Depends(get_db_session)):
        self.db: AsyncSession = db

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[models.User]:
        result = await self.db.execute(select(models.User).offset(skip).limit(limit))
        return result.scalars().all()

    async def get_user(self, user_id: int) -> models.User:
        result = await self.db.execute(select(models.User).filter(models.User.id == user_id))
        result = result.scalars().first()
        if result is None:
            raise HTTPException(status_code=404, detail="Not Found User")
        return result

    async def get_user_by_email(self, email: str) -> models.User:
        result = await self.db.execute(select(models.User).filter(models.User.email == email))
        return result.scalars().first()

    async def create_user(self, user: schemas.SignUp) -> models.User:
        hashed_password = await security.get_password_hash(user.password)

        db_user = models.User(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            hashed_password=hashed_password
        )

        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def create_user_by_email(self, email: str) -> models.User:
        db_user = models.User(
            email=email
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def update_user_info(self, user_id: int, update_data: schemas.UserInfoUpdate) -> models.User:
        user = await self.get_user(user_id=user_id)

        if update_data.first_name is not None:
            user.first_name = update_data.first_name
        if update_data.last_name is not None:
            user.last_name = update_data.last_name

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_user_password(
            self, user_id: int, update_data: schemas.UserPasswordUpdate
    ) -> Union[models.User, bool]:
        user = await self.get_user(user_id=user_id)

        if await security.verify_password(update_data.password, user.hashed_password):
            return False

        hashed_password = await security.get_password_hash(update_data.password)
        user.hashed_password = hashed_password

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete_user(self, user_id: int):
        user = await self.get_user(user_id=user_id)
        await self.db.delete(user)
        await self.db.commit()

    async def authenticate(self, login_data: schemas.SignIn) -> Optional[models.User]:
        user = await self.get_user_by_email(email=login_data.email)
        if not user:
            return None
        if not await security.verify_password(login_data.password, user.hashed_password):
            return None
        return user
