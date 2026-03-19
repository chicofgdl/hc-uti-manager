from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from sqlalchemy import select
from typing import Optional
from models.user import User
import bcrypt

class UserProvider:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, username: str, password: str, role: str) -> None:
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_user = User(username=username, hashed_password=hashed, role=role)
        self.session.add(new_user)
        await self.session.commit()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        user = await self.get_user_by_username(username)
        if user and bcrypt.checkpw(password.encode('utf-8'), user.hashed_password.encode('utf-8')):
            return {
                "username": user.username,
                "groups": [user.role],
                "email": f"{user.username}@local.com"
            }
        return None