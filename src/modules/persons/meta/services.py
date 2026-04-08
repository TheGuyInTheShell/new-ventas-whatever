from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import MetaPerson
from .schemas import RQMetaPerson

class PersonsMetaService(Service):
    async def create_meta_person(
        self,
        db: AsyncSession,
        meta: RQMetaPerson,
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

