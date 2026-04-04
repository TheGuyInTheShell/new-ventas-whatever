from sqlalchemy.ext.asyncio import AsyncSession

from .models import Options


async def create_options(
    db: AsyncSession,
    name: str,
) -> Options:
    """
    Create a new options in the database.
    
    Args:
        db: Database session
        name: Name of the options
        description: Description of the options
        
    Returns:
        Options: The created options
    """
    options_obj = Options(
        name=name,
    )
    await options_obj.save(db)
    return options_obj
