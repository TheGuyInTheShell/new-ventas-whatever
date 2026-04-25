from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import MetaComparisonValue
from .schemas import RQMetaComparisonValue

class ComparisonValuesMetaService(Service):
    @injectable
    async def create_meta_comparison_value(
        self,
        meta: RQMetaComparisonValue,
        db: AsyncSession = Depends(get_async_db),
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

