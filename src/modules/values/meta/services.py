from sqlalchemy.ext.asyncio import AsyncSession

from .models import MetaValue
from .schemas import RQMetaValue


async def create_meta(
    db: AsyncSession,
    meta: RQMetaValue,
) -> MetaValue:
    """
    Create a new meta in the database.
    
    Args:
        db: Database session
        meta: MetaValue schema
        
    Returns:
        MetaValue: The created meta
    """
    meta_obj = MetaValue(
        **meta.model_dump(),
    )
    await meta_obj.save(db)
    return meta_obj
