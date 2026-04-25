from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import MetaTransaction
from .schemas import RQMetaTransaction

class TransactionsMetaService(Service):
    @injectable
    async def create_meta_transaction(
        self,
        meta: RQMetaTransaction,
        db: AsyncSession = Depends(get_async_db),
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

