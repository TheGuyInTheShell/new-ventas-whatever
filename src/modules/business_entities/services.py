from sqlalchemy.ext.asyncio import AsyncSession
from .models import BusinessEntity
from .schemas import RQBusinessEntity

async def create_business_entity(
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
