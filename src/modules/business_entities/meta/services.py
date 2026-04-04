from sqlalchemy.ext.asyncio import AsyncSession

from .models import MetaBusinessEntity
from .schemas import RQMetaBusinessEntity


async def create_meta_business_entity(
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
