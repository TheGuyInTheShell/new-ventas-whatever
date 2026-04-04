from sqlalchemy.ext.asyncio import AsyncSession

from .models import MetaTransaction
from .schemas import RQMetaTransaction


async def create_meta_transaction(
    db: AsyncSession,
    meta: RQMetaTransaction,
) -> MetaTransaction:
    """
    Create a new meta transaction in the database.
    
    Args:
        db: Database session
        meta: MetaValue schema
        
    Returns:
        MetaTransaction: The created meta transaction
    """
    meta_obj = MetaTransaction(
        **meta.model_dump(),
    )
    await meta_obj.save(db)
    return meta_obj
