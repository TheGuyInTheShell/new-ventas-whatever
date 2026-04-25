from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import MetaValue
from .schemas import RQMetaValue

class ValuesMetaService(Service):
    @injectable
    async def create_meta(
        self,
        meta: RQMetaValue,
        db: AsyncSession = Depends(get_async_db),
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

