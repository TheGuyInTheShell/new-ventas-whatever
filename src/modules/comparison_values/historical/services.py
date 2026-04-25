from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import ComparisonValueHistorical
from .schemas import RQHistoricalComparisonValue

class ComparisonValuesHistoricalService(Service):
    @injectable
    async def create_historical(
        self,
        historical: RQHistoricalComparisonValue,
        db: AsyncSession = Depends(get_async_db),
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

