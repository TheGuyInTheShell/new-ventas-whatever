from sqlalchemy.ext.asyncio import AsyncSession

from .models import MetaComparisonValuesHistorical


async def create_meta_comparison_values_historical(
    db: AsyncSession,
    key: str,
    value: str,
    ref_comparison_value_historical: int,
) -> MetaComparisonValuesHistorical:
    """
    Create a new meta comparison values historical in the database.
    
    Args:
        db: Database session
        key: Key of the meta
        value: Value of the meta
        ref_comparison_value_historical: Reference to the comparison value historical
        
    Returns:
        MetaComparisonValuesHistorical: The created meta
    """
    meta_obj = MetaComparisonValuesHistorical(
        key=key,
        value=value,
        ref_comparison_value_historical=ref_comparison_value_historical,
    )
    await meta_obj.save(db)
    return meta_obj
