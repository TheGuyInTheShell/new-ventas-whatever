from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import ComparisonValueHistorical
from .schemas import RQHistoricalComparisonValue

class ComparisonValuesHistoricalService(Service):
    async def create_historical(
        self,
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

