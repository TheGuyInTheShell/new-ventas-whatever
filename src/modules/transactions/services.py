from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import TYPE_CHECKING, List

from core.lib.register.service import Service
from core.lib.decorators.services import Services

from .models import Transaction
from .schemas import RQTransaction
from ..comparison_values.models import ComparisonValue
from ..comparison_values.services import ComparisonValuesService

if TYPE_CHECKING:
    from .schemas import RQSale

@Services(ComparisonValuesService)
class TransactionsService(Service):
    ComparisonValuesService: ComparisonValuesService

    @injectable
    async def create_transaction(
        self,
        transaction_data: RQTransaction,
        db: AsyncSession = Depends(get_async_db),
    ) -> Transaction:
        transaction = Transaction(
            quantity=transaction_data.quantity,
            operation_type=transaction_data.operation_type,
            reference_code=transaction_data.reference_code,
            ref_by_user=transaction_data.ref_by_user,
            ref_value_from=transaction_data.ref_value_from,
            ref_value_to=transaction_data.ref_value_to,
            ref_business_entity_from=transaction_data.ref_business_entity_from,
            ref_business_entity_to=transaction_data.ref_business_entity_to,
            ref_balance_from=transaction_data.ref_balance_from,
            ref_balance_to=transaction_data.ref_balance_to,
            ref_comparation_values_historical=transaction_data.ref_comparation_values_historical
        )
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        return transaction

    @injectable
    async def process_sale(
        self,
        sale_data: "RQSale",
        db: AsyncSession = Depends(get_async_db),
    ) -> List[Transaction]:
        """
        Process a sale:
        For each item:
        1. Find active price comparison (Item -> Currency).
        2. Create historical snapshot of that price.
        3. Create transaction linked to that snapshot.
        """
        transactions = []
        
        for item in sale_data.items:
            # Find active comparison for price (Item -> Currency)
            query = select(ComparisonValue).where(
                ComparisonValue.value_from == item.value_id,
                ComparisonValue.value_to == sale_data.currency_id,
                ComparisonValue.is_deleted == False
            )
            comparison = (await db.execute(query)).scalar_one_or_none()
            
            if not comparison:
                raise ValueError(f"No price comparison found for value {item.value_id} to currency {sale_data.currency_id}")
                
            # Create snapshot
            historical = await self.ComparisonValuesService.create_historical_snapshot(comparison)
            
            # Create Transaction
            transaction = Transaction(
                quantity=str(item.quantity),
                operation_type="+", 
                reference_code=sale_data.reference_code,
                ref_by_user=sale_data.ref_by_user,
                ref_value_from=item.value_id, # Item
                ref_value_to=sale_data.currency_id, # Currency
                ref_business_entity_from=sale_data.ref_business_entity_from,
                ref_business_entity_to=sale_data.ref_business_entity_to,
                ref_balance_from=sale_data.ref_balance_from,
                ref_balance_to=sale_data.ref_balance_to,
                ref_comparation_values_historical=historical.id
            )
            db.add(transaction)
            transactions.append(transaction)
            
        await db.commit()
        for t in transactions:
            await db.refresh(t)
            
        return transactions

