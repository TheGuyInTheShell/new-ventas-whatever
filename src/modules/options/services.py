from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import Options
from .schemas import Option
from fastapi import Depends
from core.database import get_async_db
from fastapi_injectable import injectable

class OptionsService(Service):
    
    @injectable
    async def create_options(
        self,
        name: str,
        context: str,
        value: str,
        db: AsyncSession = Depends(get_async_db),
    ) -> Option:
        """
        Create a new options in the database.
        
        Args:
            db: Database session
            name: Name of the options
            
        Returns:
            Option: The created options
        """
        options_obj = Options(
            name=name,
            context=context,
            value=value,
        )
        await options_obj.save(db)
        await db.refresh(options_obj)
        return Option(
            id=options_obj.id,
            uid=options_obj.uid,
            name=options_obj.name,
            context=options_obj.context,
            value=options_obj.value
        )
