from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import MetaBusinessEntity
from .schemas import RQMetaBusinessEntity

class BusinessEntitiesMetaService(Service):
    async def create_meta_business_entity(
        self,
        db: AsyncSession,
        meta: RQMetaBusinessEntity,
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

