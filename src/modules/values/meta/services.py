from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import MetaValue
from .schemas import RQMetaValue

class ValuesMetaService(Service):
    async def create_meta(
        self,
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

