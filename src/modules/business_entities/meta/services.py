from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import MetaBusinessEntity
from .schemas import RQMetaBusinessEntity

class BusinessEntitiesMetaService(Service):
    @injectable
    async def create_meta_business_entity(
        self,
        meta: RQMetaBusinessEntity,
        db: AsyncSession = Depends(get_async_db),
    ) -> MetaBusinessEntity:
        """
        Create a new meta business entity in the database.
        
        Args:
            db: Database session
            meta: MetaValue schema
            
        Returns:
            MetaBusinessEntity: The created meta business entity
        """
        meta_obj = MetaBusinessEntity(
            **meta.model_dump(),
        )
        await meta_obj.save(db)
        return meta_obj

