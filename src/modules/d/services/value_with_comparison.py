from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from typing import Optional, TYPE_CHECKING
from src.modules.values.services import create_value_with_meta, update_value_with_meta
from src.modules.comparison_values.services import create_comparison, update_comparison
from src.modules.values.schemas import RSValue
from src.modules.comparison_values.schemas import RSComparisonValue
from src.modules.d.schemas.values_with_comparison import RQValueWithComparison, RSValueWithComparison, QueryValuesWithComparison, ResultValueWithComparison
from src.modules.d.models.values_with_comparison import BuilderValueWithComparison

from src.modules.values.hierarchy.models import ValuesHierarchy
from src.modules.balances.models import Balance
from src.modules.balances_business_entities.models import BalanceBusinessEntity

from sqlalchemy import delete

if TYPE_CHECKING:
    from src.modules.values.models import Value
    from src.modules.comparison_values.models import ComparisonValue

async def save_value_with_comparison_service(db: AsyncSession, data: RQValueWithComparison) -> RSValueWithComparison:
    """
    Saves a value (and its meta data) and a comparison (and its meta data).
    The comparison automatically uses the newly created value as its source if not provided.
    Also handles optional linking to an inventory value and auto-creating balances.
    """
    try:
        saved_value = await create_value_with_meta(db, data.value)
        
        if data.comparison_value.value_from is None:
            data.comparison_value.value_from = saved_value.id
            
        saved_comparison = await create_comparison(db, data.comparison_value)
        
        # 1. Hierarchy: link to all superior values (composite parent links)
        for super_id in (data.ref_super_values_ids or []):
            hierarchy = ValuesHierarchy(
                ref_value_top=super_id,
                ref_value_bottom=saved_value.id
            )
            db.add(hierarchy)
        
        # 2. Balance: auto-create an inventory balance for this value
        new_balance = Balance(
            quantity=0,
            type="Basic",
            ref_value=saved_value.id
        )
        db.add(new_balance)
        await db.flush() # flush to get new_balance.id
        
        # 3. BalanceBusinessEntity: link the balance to the specific entities
        if data.business_entity_ids:
            for entity_id in data.business_entity_ids:
                bal_ent = BalanceBusinessEntity(
                    ref_balance=new_balance.id,
                    ref_business_entity=entity_id
                )
                db.add(bal_ent)
        
        await db.commit()
        await db.refresh(saved_value)
        await db.refresh(saved_comparison)

        return RSValueWithComparison(
            value=RSValue(
                uid=saved_value.uid,
                id=saved_value.id,
                name=saved_value.name,
                expression=saved_value.expression,
                type=saved_value.type,
                context=saved_value.context,
                identifier=saved_value.identifier
            ),
            comparison_value=RSComparisonValue(
                uid=saved_comparison.uid,
                id=saved_comparison.id,
                quantity_from=saved_comparison.quantity_from,
                quantity_to=saved_comparison.quantity_to,
                value_from=saved_comparison.value_from,
                value_to=saved_comparison.value_to,
                context=saved_comparison.context
            )
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


async def update_value_with_comparison_service(db: AsyncSession, id: str, data: RQValueWithComparison) -> RSValueWithComparison:
    """
    Updates a value and a comparison.
    Also syncs the optional inventory hierarchy and balance business entities.
    """
    try:
        # Assuming the value and comparison updates handle finding the record by id (uid)
        updated_value = await update_value_with_meta(db, id, data.value)
        
        # Determine the comparison value ID from the DB or payload
        # Wait, comparison update usually takes its own ID, but here the 'id' is for the Value.
        # We need to find the existing ComparisonValue where value_from == updated_value.id
        # For simplicity, using query builder or direct select:
        from sqlalchemy import select
        from src.modules.comparison_values.models import ComparisonValue
        
        stmt = select(ComparisonValue).where(ComparisonValue.value_from == updated_value.id)
        result = await db.execute(stmt)
        existing_comparison = result.scalars().first()
        
        if existing_comparison:
            updated_comparison = await update_comparison(db, existing_comparison.uid, data.comparison_value)
        else:
            if data.comparison_value.value_from is None:
                data.comparison_value.value_from = updated_value.id
            updated_comparison = await create_comparison(db, data.comparison_value)

        # 1. Sync Hierarchy: replace all parent links with the provided list
        if data.ref_super_values_ids is not None:
            # Delete all existing parent links for this value
            await db.execute(delete(ValuesHierarchy).where(ValuesHierarchy.ref_value_bottom == updated_value.id))
            # Insert new links for each superior value
            for super_id in data.ref_super_values_ids:
                hierarchy = ValuesHierarchy(
                    ref_value_top=super_id,
                    ref_value_bottom=updated_value.id
                )
                db.add(hierarchy)
        
        # 2. Sync BalanceBusinessEntity
        # First find the Balance for this value
        balance_stmt = select(Balance).where(Balance.ref_value == updated_value.id).where(Balance.type == 'inventory')
        bal_result = await db.execute(balance_stmt)
        existing_balance = bal_result.scalars().first()
        
        if existing_balance and data.business_entity_ids is not None:
            # Delete existings links
            await db.execute(delete(BalanceBusinessEntity).where(BalanceBusinessEntity.ref_balance == existing_balance.id))
            # Insert new links
            for entity_id in data.business_entity_ids:
                bal_ent = BalanceBusinessEntity(
                    ref_balance=existing_balance.id,
                    ref_business_entity=entity_id
                )
                db.add(bal_ent)
        elif not existing_balance:
            # Create a balance if it didn't exist for some reason
            new_balance = Balance(
                currency="unit",
                type="inventory",
                ref_value=updated_value.id
            )
            db.add(new_balance)
            await db.flush()
            if data.business_entity_ids:
                for entity_id in data.business_entity_ids:
                    bal_ent = BalanceBusinessEntity(
                        ref_balance=new_balance.id,
                        ref_business_entity=entity_id
                    )
                    db.add(bal_ent)

        await db.commit()
        await db.refresh(updated_value)
        await db.refresh(updated_comparison)

        return RSValueWithComparison(
            value=RSValue(
                uid=updated_value.uid,
                id=updated_value.id,
                name=updated_value.name,
                expression=updated_value.expression,
                type=updated_value.type,
                context=updated_value.context,
                identifier=updated_value.identifier
            ),
            comparison_value=RSComparisonValue(
                uid=updated_comparison.uid,
                id=updated_comparison.id,
                quantity_from=updated_comparison.quantity_from,
                quantity_to=updated_comparison.quantity_to,
                value_from=updated_comparison.value_from,
                value_to=updated_comparison.value_to,
                context=updated_comparison.context
            )
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

async def get_values_with_comparison_service(db: AsyncSession, data: QueryValuesWithComparison) -> ResultValueWithComparison:
    """
    Query values and comparison values dynamically based on provided filters.
    """
    builder = BuilderValueWithComparison(db)
    result = await builder.set_query(data).build().execute()
    return result
