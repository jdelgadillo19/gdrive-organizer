import uuid

from sqlalchemy import select

from kip_core.db.models.user import User
from kip_core.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, email: str, role: str = "viewer") -> User:
        user = User(email=email, role=role)
        self._session.add(user)
        await self._session.flush()
        return user
