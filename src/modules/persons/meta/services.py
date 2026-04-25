from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import MetaPerson
from .schemas import RQMetaPerson

class PersonsMetaService(Service):
    @injectable
    async def create_meta_person(
        self,
        meta: RQMetaPerson,
        db: AsyncSession = Depends(get_async_db),
    ) -> MetaPerson:
        """
        Create a new meta person in the database.
        
        Args:
            db: Database session
            meta: MetaPerson schema
            
        Returns:
            MetaPerson: The created meta person
        """
        meta_obj = MetaPerson(
            **meta.model_dump(),
        )
        await meta_obj.save(db)
        return meta_obj

