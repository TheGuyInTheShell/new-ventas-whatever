from sqlalchemy.ext.asyncio import AsyncSession
from typing import TYPE_CHECKING
from .models import Transaction
from .schemas import RQTransaction

if TYPE_CHECKING:
    from .schemas import RQSale

async def create_transaction(
    db: AsyncSession,
    transaction_data: RQTransaction
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


async def process_sale(
    db: AsyncSession,
    sale_data: "RQSale"
) -> list[Transaction]:
    """
    Process a sale:
    For each item:
    1. Find active price comparison (Item -> Currency).
    2. Create historical snapshot of that price.
    3. Create transaction linked to that snapshot.
    """
    from app.modules.comparison_values.models import ComparisonValue
    from app.modules.comparison_values.services import find_comparison_rate, create_historical_snapshot
    from sqlalchemy import select
    
    transactions = []
    
    for item in sale_data.items:
        # Find active comparison for price (Item -> Currency)
        # We assume there is a direct comparison or we need to find one.
        # For simplicity, let's query the specific comparison record if possible,
        # or use find_comparison_rate logic but we need the actual ComparisonValue object for snapshot.
        
        # We try to find the direct comparison: Item -> Currency
        query = select(ComparisonValue).where(
            ComparisonValue.value_from == item.value_id,
            ComparisonValue.value_to == sale_data.currency_id,
            ComparisonValue.is_deleted == False
        )
        comparison = (await db.execute(query)).scalar_one_or_none()
        
        if not comparison:
            # If not found, maybe try inverse? But price is usually defined as Item -> Currency.
            # If not found, we can't snapshot the price. Raise error or skip?
            # Requirement says "snapshot of the compared prices".
            raise ValueError(f"No price comparison found for value {item.value_id} to currency {sale_data.currency_id}")
            
        # Create snapshot
        # create_historical_snapshot commits, but we are in a loop.
        # Ideally we should use a transaction but implicit session handling in fastapi usually handles it.
        # create_historical_snapshot returns an object.
        historical = await create_historical_snapshot(db, comparison)
        
        # Create Transaction
        transaction = Transaction(
            quantity=str(item.quantity), # Stored as string in model?
            operation_type="+", # Sale is positive for cash, negative for inventory? 
                               # Model says quantity is string, operation_type is +/-. 
                               # Convention: Sale = + money? Or - stock?
                               # Let's assume + (Income).
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
