from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import BusinessEntity
from .schemas import RQBusinessEntity

class BusinessEntitiesService(Service):
    @injectable
    async def create_business_entity(
        self,
        entity_data: RQBusinessEntity,
        db: AsyncSession = Depends(get_async_db)
    ) -> BusinessEntity:
        entity = BusinessEntity(
            name=entity_data.name,
            type=entity_data.type,
            context=entity_data.context,
            metadata_info=entity_data.metadata_info
        )
        await entity.save(db)
        return entity

