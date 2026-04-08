from typing import List, Optional, Literal

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from core.lib.decorators import Get, Post, Delete, Put
from core.lib.register import Controller

from src.modules.transactions.models import Transaction
from src.modules.transactions.schemas import RQTransaction, RSTransaction, RSTransactionList, RQSale
from src.modules.transactions.services import create_transaction


class TransactionsController(Controller):
    """
    Controller for Transactions management.
    
    Path: /api/v1/transactions
    """

    @Get("/id/{id}", response_model=RSTransaction, status_code=200)
    async def get_Transaction(
        self, id: str, db: AsyncSession = Depends(get_async_db)
    ) -> RSTransaction:
        try:
            result: Transaction = await Transaction.find_one(db, id)
            return RSTransaction(
                id=result.id,
                uid=result.uid,
                quantity=result.quantity,
                operation_type=result.operation_type,
                reference_code=result.reference_code,
                ref_by_user=result.ref_by_user,
                ref_value_from=result.ref_value_from,
                ref_value_to=result.ref_value_to,
                ref_business_entity_from=result.ref_business_entity_from,
                ref_business_entity_to=result.ref_business_entity_to,
                ref_balance_from=result.ref_balance_from,
                ref_balance_to=result.ref_balance_to,
                ref_comparation_values_historical=result.ref_comparation_values_historical,
            )
        except Exception as e:
            print(e)
            raise e

    @Get("/", response_model=List[RSTransaction], status_code=200)
    async def get_Transactions(
        self,
        pag: Optional[int] = 1,
        ord: Literal["asc", "desc"] = "asc",
        status: Literal["deleted", "exists", "all"] = "exists",
        db: AsyncSession = Depends(get_async_db),
    ) -> RSTransactionList:
        try:
            result = await Transaction.find_some(db, pag or 1, ord, status)
            mapped_result = map(
                lambda x: RSTransaction(
                    uid=x.uid,
                    id=x.id,
                    quantity=x.quantity,
                    operation_type=x.operation_type,
                    reference_code=x.reference_code,
                    ref_by_user=x.ref_by_user,
                    ref_value_from=x.ref_value_from,
                    ref_value_to=x.ref_value_to,
                    ref_business_entity_from=x.ref_business_entity_from,
                    ref_business_entity_to=x.ref_business_entity_to,
                    ref_balance_from=x.ref_balance_from,
                    ref_balance_to=x.ref_balance_to,
                    ref_comparation_values_historical=x.ref_comparation_values_historical,
                ),
                result,
            )
            return RSTransactionList(
                data=list(mapped_result),
                total=0,
                page=0,
                page_size=0,
                total_pages=0,
                has_next=False,
                has_prev=False,
                next_page=0,
                prev_page=0,
            )
        except Exception as e:
            print(e)
            raise e

    @Post("/", response_model=RSTransaction, status_code=201)
    async def create_Transaction_endpoint(
        self, transaction: RQTransaction, db: AsyncSession = Depends(get_async_db)
    ) -> RSTransaction:
        try:
            result = await create_transaction(db, transaction)
            return RSTransaction(
                id=result.id,
                uid=result.uid,
                quantity=result.quantity,
                operation_type=result.operation_type,
                reference_code=result.reference_code,
                ref_by_user=result.ref_by_user,
                ref_value_from=result.ref_value_from,
                ref_value_to=result.ref_value_to,
                ref_business_entity_from=result.ref_business_entity_from,
                ref_business_entity_to=result.ref_business_entity_to,
                ref_balance_from=result.ref_balance_from,
                ref_balance_to=result.ref_balance_to,
                ref_comparation_values_historical=result.ref_comparation_values_historical,
            )
        except Exception as e:
            print(e)
            raise e

    @Post("/sale", response_model=List[RSTransaction], status_code=201)
    async def create_sale_endpoint(
        self, sale: RQSale, db: AsyncSession = Depends(get_async_db)
    ) -> List[RSTransaction]:
        """
        Register a sale transaction.
        Creates transactions for each item and snapshots their prices.
        """
        try:
            from src.modules.transactions.services import process_sale
            results = await process_sale(db, sale)
            
            return [
                RSTransaction(
                    id=t.id,
                    uid=t.uid,
                    quantity=t.quantity,
                    operation_type=t.operation_type,
                    reference_code=t.reference_code,
                    ref_by_user=t.ref_by_user,
                    ref_value_from=t.ref_value_from,
                    ref_value_to=t.ref_value_to,
                    ref_business_entity_from=t.ref_business_entity_from,
                    ref_business_entity_to=t.ref_business_entity_to,
                    ref_balance_from=t.ref_balance_from,
                    ref_balance_to=t.ref_balance_to,
                    ref_comparation_values_historical=t.ref_comparation_values_historical,
                )
                for t in results
            ]
        except Exception as e:
            print(e)
            raise e

    @Delete("/id/{id}", status_code=204)
    async def delete_Transaction(self, id: str, db: AsyncSession = Depends(get_async_db)) -> None:
        try:
            await Transaction.delete(db, id)
        except Exception as e:
            print(e)
            raise e

    @Put("/id/{id}", response_model=RSTransaction, status_code=200)
    async def update_Transaction(
        self, id: str, transaction: RQTransaction, db: AsyncSession = Depends(get_async_db)
    ) -> RSTransaction:
        try:
            result = await Transaction.update(db, id, transaction.model_dump())
            return RSTransaction(
                id=result.id,
                uid=result.uid,
                quantity=result.quantity,
                operation_type=result.operation_type,
                reference_code=result.reference_code,
                ref_by_user=result.ref_by_user,
                ref_value_from=result.ref_value_from,
                ref_value_to=result.ref_value_to,
                ref_business_entity_from=result.ref_business_entity_from,
                ref_business_entity_to=result.ref_business_entity_to,
                ref_balance_from=result.ref_balance_from,
                ref_balance_to=result.ref_balance_to,
                ref_comparation_values_historical=result.ref_comparation_values_historical,
            )
        except Exception as e:
            print(e)
            raise e
