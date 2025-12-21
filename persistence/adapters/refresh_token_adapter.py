from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update, delete, false, true
from sqlalchemy.ext.asyncio import AsyncSession

from core.persistence.refresh_token_repository_port import RefreshTokenRepositoryPort
from domain.refresh_token import RefreshToken
from persistence.mappers.refresh_token_mapper import RefreshTokenMapper
from persistence.model.refresh_token_entity import RefreshTokenEntity


class RefreshTokenRepositoryAdapter(RefreshTokenRepositoryPort):
    def __init__(self, session: AsyncSession, mapper: RefreshTokenMapper):
        self.session = session
        self.mapper = mapper

    async def save(self, refresh_token: RefreshToken) -> RefreshToken:
        entity = self.mapper.to_entity(refresh_token)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return self.mapper.to_domain(entity)

    async def get(self, token_id: UUID) -> Optional[RefreshToken]:
        query = select(RefreshTokenEntity).where(RefreshTokenEntity.id == token_id)
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def find_by_token(self, token: str) -> Optional[RefreshToken]:
        query = select(RefreshTokenEntity).where(RefreshTokenEntity.token == token)
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()
        return self.mapper.to_domain(entity) if entity else None

    async def find_active_by_user(self, user_id: UUID) -> List[RefreshToken]:
        query = (
            select(RefreshTokenEntity)
            .where(
                RefreshTokenEntity.user_id == user_id,
                RefreshTokenEntity.revoked.is_(false()),
                RefreshTokenEntity.active.is_(true()),
                RefreshTokenEntity.expires_at > datetime.now(),
            )
            .order_by(RefreshTokenEntity.created_at.desc())
        )

        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(e) for e in entities]

    async def revoke_all_by_user(self, user_id: UUID) -> int:
        query = (
            update(RefreshTokenEntity)
            .where(
                RefreshTokenEntity.user_id == user_id,
                RefreshTokenEntity.revoked.is_(false()),
            )
            .values(revoked=True, revoked_at=datetime.now(), modified_at=datetime.now())
        )

        result = await self.session.execute(query)
        await self.session.flush()
        return result.rowcount

    async def delete_expired(self) -> int:
        query = delete(RefreshTokenEntity).where(
            RefreshTokenEntity.expires_at < datetime.now()
        )

        result = await self.session.execute(query)
        await self.session.flush()
        return result.rowcount

    async def find_all(self) -> List[RefreshToken]:
        query = select(RefreshTokenEntity).order_by(
            RefreshTokenEntity.created_at.desc()
        )

        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [self.mapper.to_domain(e) for e in entities]

    async def count_active_by_user(self, user_id: UUID) -> int:
        from sqlalchemy import func

        query = select(func.count(RefreshTokenEntity.id)).where(
            RefreshTokenEntity.user_id == user_id,
            RefreshTokenEntity.revoked.is_(false()),
            RefreshTokenEntity.active.is_(true()),
            RefreshTokenEntity.expires_at > datetime.now(),
        )

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def revoke_token_by_id(self, token_id: UUID) -> bool:
        query = (
            update(RefreshTokenEntity)
            .where(
                RefreshTokenEntity.id == token_id, RefreshTokenEntity.revoked.is_(false()),
            )
            .values(revoked=True, revoked_at=datetime.now(), modified_at=datetime.now())
        )

        result = await self.session.execute(query)
        await self.session.flush()
        return result.rowcount > 0
