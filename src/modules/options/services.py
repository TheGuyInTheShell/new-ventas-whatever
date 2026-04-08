from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import Options

class OptionsService(Service):
    async def create_options(
        self,
        db: AsyncSession,
        name: str,
    ) -> Options:
        """
        Create a new options in the database.
        
        Args:
            db: Database session
            name: Name of the options
            
        Returns:
            Options: The created options
        """
        options_obj = Options(
            name=name,
        )
        await options_obj.save(db)
        return options_obj

