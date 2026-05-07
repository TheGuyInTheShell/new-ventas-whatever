from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Tuple, Any

from core.lib.register.service import Service
from core.lib.decorators.services import Services
from fastapi import Depends
from fastapi_injectable import injectable

from core.lib.decorators.exceptions import handle_service_errors, ServiceResult
from core.database import get_async_db, SessionAsync

from ...values.services import ValuesService
from ...comparison_values.services import ComparisonValuesService
from ...values.schemas import RSValue
from ...comparison_values.schemas import RSComparisonValue
from ..schemas.values_with_comparison import (
    RQValueWithComparison,
    RSValueWithComparison,
    QueryValuesWithComparison,
    ResultValueWithComparison,
)
from ..models.values_with_comparison import BuilderValueWithComparison
from ..exceptions.value_with_comparison import (
    ComparisonCreationFailedError,
    ComparisonUpdateFailedError,
)
from ...values.hierarchy.models import ValuesHierarchy
from ...balances.models import Balance, BalanceType
from ...balances_business_entities.models import BalanceBusinessEntity
from ...comparison_values.models import ComparisonValue
from ...comparison_values.meta.models import MetaComparisonValue
from ..hooks.value_with_comparison import on_value_with_comparison_updated, trigger_value_with_comparison_updated


@Services(ValuesService, ComparisonValuesService)
class DValueWithComparisonService(Service):
    ValuesService: ValuesService
    ComparisonValuesService: ComparisonValuesService

    @handle_service_errors
    @injectable
    async def save_value_with_comparison_service(
        self, data: RQValueWithComparison, db: AsyncSession = Depends(get_async_db)
    ) -> ServiceResult[RSValueWithComparison]:
        """
        Saves a value (and its meta data) and a comparison (and its meta data).
        The comparison automatically uses the newly created value as its source if not provided.
        Also handles optional linking to an inventory value and auto-creating balances.
        """
        saved_value, error = await self.ValuesService.create_value_with_meta(data.value)
        if error:
            return None, error

        if saved_value is None:
            return None, ComparisonCreationFailedError("Failed to create value")

        if data.comparison_value.value_from is None:
            data.comparison_value.value_from = saved_value.id

        saved_comparison, error = await self.ComparisonValuesService.create_comparison(
            data.comparison_value, db=db
        )
        if error or not saved_comparison:
            await db.rollback()
            return None, error or ComparisonCreationFailedError(
                "Failed to create comparison"
            )

        # 1. Hierarchy: link to all superior values (composite parent links)
        for super_id in data.ref_super_values_ids or []:
            hierarchy = ValuesHierarchy(
                ref_value_top=super_id, ref_value_bottom=saved_value.id
            )
            db.add(hierarchy)

        # 2. Balance: auto-create a balance for this value using the provided type
        if data.balance_type:
            new_balance = Balance(
                quantity=0, type=data.balance_type, ref_value=saved_value.id
            )
            db.add(new_balance)
            await db.flush()  # flush to get new_balance.id

        # 3. BalanceBusinessEntity: link the balance to the specific entities
        if data.balance_type and data.business_entity_ids:
            for entity_id in data.business_entity_ids:
                bal_ent = BalanceBusinessEntity(
                    ref_balance=new_balance.id, ref_business_entity=entity_id
                )
                db.add(bal_ent)

        await db.commit()
        await db.refresh(saved_value)
        await db.refresh(saved_comparison)

        return (
            RSValueWithComparison(
                value=RSValue(
                    uid=saved_value.uid,
                    id=saved_value.id,
                    name=saved_value.name,
                    expression=saved_value.expression,
                    type=saved_value.type,
                    ref_business_entity=saved_value.ref_business_entity,
                    identifier=saved_value.identifier,
                ),
                comparison_value=RSComparisonValue(
                    uid=saved_comparison.uid,
                    id=saved_comparison.id,
                    quantity_from=saved_comparison.quantity_from,
                    quantity_to=saved_comparison.quantity_to,
                    value_from=saved_comparison.value_from,
                    value_to=saved_comparison.value_to,
                    ref_business_entity=saved_comparison.ref_business_entity,
                ),
            ),
            None,
        )

    @handle_service_errors
    @injectable
    @trigger_value_with_comparison_updated
    async def update_value_with_comparison_service(
        self,
        id: str,
        data: RQValueWithComparison,
        db: AsyncSession = Depends(get_async_db),
    ) -> ServiceResult[RSValueWithComparison]:
        """
        Updates a value and a comparison.
        Also syncs the optional inventory hierarchy and balance business entities.
        """
        # Assuming the value and comparison updates handle finding the record by id (uid)
        updated_value, error = await self.ValuesService.update_value_with_meta(
            id, data.value
        )
        if error:
            return None, error

        if updated_value is None:
            return None, ComparisonUpdateFailedError("Failed to update value")

        stmt = select(ComparisonValue).where(
            ComparisonValue.value_from == updated_value.id
        )
        result = await db.execute(stmt)
        existing_comparison = result.scalars().first()

        if existing_comparison:
            if data.comparison_value.value_from is None:
                data.comparison_value.value_from = updated_value.id
            updated_comparison, error = (
                await self.ComparisonValuesService.update_comparison(
                    existing_comparison.uid, data.comparison_value, db=db
                )
            )
            if error or not updated_comparison:
                await db.rollback()
                return None, error or ComparisonUpdateFailedError(
                    "Failed to update comparison"
                )
        else:
            if data.comparison_value.value_from is None:
                data.comparison_value.value_from = updated_value.id
            updated_comparison, error = (
                await self.ComparisonValuesService.create_comparison(
                    data.comparison_value, db=db
                )
            )
            if error or not updated_comparison:
                await db.rollback()
                return None, error or ComparisonCreationFailedError(
                    "Failed to create comparison"
                )

        # 1. Sync Hierarchy: replace all parent links with the provided list
        if data.ref_super_values_ids is not None:
            # Delete all existing parent links for this value
            await db.execute(
                delete(ValuesHierarchy).where(
                    ValuesHierarchy.ref_value_bottom == updated_value.id
                )
            )
            # Insert new links for each superior value
            for super_id in data.ref_super_values_ids:
                hierarchy = ValuesHierarchy(
                    ref_value_top=super_id, ref_value_bottom=updated_value.id
                )
                db.add(hierarchy)

        # 2. Sync BalanceBusinessEntity
        # First find the Balance for this value
        balance_stmt = (
            select(Balance)
            .where(Balance.ref_value == updated_value.id)
            .where(Balance.type == data.balance_type)
        )
        bal_result = await db.execute(balance_stmt)
        existing_balance = bal_result.scalars().first()

        if existing_balance and data.business_entity_ids is not None:
            # Delete existings links
            await db.execute(
                delete(BalanceBusinessEntity).where(
                    BalanceBusinessEntity.ref_balance == existing_balance.id
                )
            )
            # Insert new links
            for entity_id in data.business_entity_ids:
                bal_ent = BalanceBusinessEntity(
                    ref_balance=existing_balance.id, ref_business_entity=entity_id
                )
                db.add(bal_ent)
        elif not existing_balance:
            # Create a balance if it didn't exist for some reason
            new_balance = Balance(
                quantity=0, type=data.balance_type, ref_value=updated_value.id
            )
            db.add(new_balance)
            await db.flush()
            if data.business_entity_ids:
                for entity_id in data.business_entity_ids:
                    bal_ent = BalanceBusinessEntity(
                        ref_balance=new_balance.id, ref_business_entity=entity_id
                    )
                    db.add(bal_ent)

        await db.commit()
        await db.refresh(updated_value)
        await db.refresh(updated_comparison)

        return (
            RSValueWithComparison(
                value=RSValue(
                    uid=updated_value.uid,
                    id=updated_value.id,
                    name=updated_value.name,
                    expression=updated_value.expression,
                    type=updated_value.type,
                    ref_business_entity=updated_value.ref_business_entity,
                    identifier=updated_value.identifier,
                ),
                comparison_value=RSComparisonValue(
                    uid=updated_comparison.uid,
                    id=updated_comparison.id,
                    quantity_from=updated_comparison.quantity_from,
                    quantity_to=updated_comparison.quantity_to,
                    value_from=updated_comparison.value_from,
                    value_to=updated_comparison.value_to,
                    ref_business_entity=updated_comparison.ref_business_entity,
                ),
            ),
            None,
        )

    @handle_service_errors
    @injectable
    async def get_values_with_comparison_service(
        self, data: QueryValuesWithComparison, db: AsyncSession = Depends(get_async_db)
    ) -> ServiceResult[ResultValueWithComparison]:
        """
        Query values and comparison values dynamically based on provided filters.
        """
        builder = BuilderValueWithComparison(db)
        result = await builder.set_query(data).build().execute()
        return result, None


@on_value_with_comparison_updated
async def recursive_hierarchy_comparison_update(
    result: Tuple[RSValueWithComparison, Any] | RSValueWithComparison, *args, **kwargs
):
    """
    Background hook to recursively update comparison values in the hierarchy
    when a child comparison value is updated.
    """
    rs_data = None
    if isinstance(result, tuple) and len(result) == 2:
        val, err = result
        if not err and val:
            rs_data = val
    elif isinstance(result, RSValueWithComparison):
        rs_data = result

    if not rs_data:
        return

    child_value_id = rs_data.value.id
    comparison_data = rs_data.comparison_value

    async with SessionAsync() as db:
        await _update_parents_recursively(child_value_id, comparison_data, db=db)
        await db.commit()


@injectable
async def _update_parents_recursively(
    child_id: int,
    comparison_data: RSComparisonValue,
    db: AsyncSession = Depends(get_async_db),
):
    stmt = select(ValuesHierarchy.ref_value_top).where(
        ValuesHierarchy.ref_value_bottom == child_id
    )
    res = await db.execute(stmt)
    parent_ids = res.scalars().all()

    for parent_id in parent_ids:
        # Get the comparison value of the parent
        comp_stmt = select(ComparisonValue).where(
            ComparisonValue.value_from == parent_id
        )
        comp_res = await db.execute(comp_stmt)
        parent_comp = comp_res.scalars().first()

        if parent_comp:
            # Check for LOCK_UPDATE in meta_comparison
            meta_stmt = select(MetaComparisonValue).where(
                MetaComparisonValue.ref_comparison_value == parent_comp.id,
                MetaComparisonValue.key == "LOCK_UPDATE",
                MetaComparisonValue.value == "1",
            )
            meta_res = await db.execute(meta_stmt)
            if meta_res.scalars().first():
                continue  # Skip update due to lock

            # Update parent comparison fields based on the child's new comparison data
            parent_comp.quantity_to = comparison_data.quantity_to
            parent_comp.quantity_from = comparison_data.quantity_from
            parent_comp.value_to = comparison_data.value_to

            db.add(parent_comp)
            await db.flush()

            # Recurse up the hierarchy
            await _update_parents_recursively(parent_id, comparison_data, db=db)
