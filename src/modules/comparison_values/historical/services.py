from sqlalchemy.ext.asyncio import AsyncSession

from .models import ComparisonValueHistorical
from .schemas import RQHistoricalComparisonValue


async def create_historical(
    db: AsyncSession,
    historical: RQHistoricalComparisonValue,
) -> ComparisonValueHistorical:
    """
    Create a new comparison value historical in the database.
    
    Args:
        db: Database session
        historical: Historical schema
        
    Returns:
        ComparisonValueHistorical: The created historical
    """
    historical_obj = ComparisonValueHistorical(
        **historical.model_dump(),
    )
    await historical_obj.save(db)
    return historical_obj
