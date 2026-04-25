from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import MetaComparisonValuesHistorical

class ComparisonValuesHistoricalMetaService(Service):
    @injectable
    async def create_meta_comparison_values_historical(
        self,
        key: str,
        value: str,
        ref_comparison_value_historical: int,
        db: AsyncSession = Depends(get_async_db),
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

