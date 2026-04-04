from sqlalchemy.ext.asyncio import AsyncSession

from .models import MetaComparisonValue
from .schemas import RQMetaComparisonValue


async def create_meta_comparison_value(
    db: AsyncSession,
    meta: RQMetaComparisonValue,
) -> MetaComparisonValue:
    """
    Create a new meta comparison value in the database.
    
    Args:
        db: Database session
        meta: MetaComparisonValue schema
        
    Returns:
        MetaComparisonValue: The created meta comparison value
    """
    meta_obj = MetaComparisonValue(
        **meta.model_dump(),
    )
    await meta_obj.save(db)
    return meta_obj
