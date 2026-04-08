from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import BusinessEntity
from .schemas import RQBusinessEntity

class BusinessEntitiesService(Service):
    async def create_business_entity(
        self,
        db: AsyncSession,
        entity_data: RQBusinessEntity
    ) -> BusinessEntity:
        entity = BusinessEntity(
            name=entity_data.name,
            type=entity_data.type,
            context=entity_data.context,
            metadata_info=entity_data.metadata_info
        )
        await entity.save(db)
        return entity

