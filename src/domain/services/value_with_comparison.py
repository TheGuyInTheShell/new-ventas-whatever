from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Tuple, Any, Sequence

from core.lib.register.service import Service
from core.lib.decorators.services import Services
from fastapi import Depends
from fastapi_injectable import injectable

from core.lib.decorators.exceptions import handle_service_errors, ServiceResult
from core.database import get_async_db, SessionAsync

from src.modules.values.services import ValuesService
from src.modules.comparison_values.services import ComparisonValuesService
from src.modules.values.schemas import RSValue
from src.modules.comparison_values.schemas import RSComparisonValue
from src.domain.schemas.values_with_comparison import (
    RQValueWithComparison,
    RSValueWithComparison,
    QueryValuesWithComparison,
    ResultValueWithComparison,
)
from src.domain.models.values_with_comparison import BuilderValueWithComparison
from src.domain.exceptions.value_with_comparison import (
    ComparisonCreationFailedError,
    ComparisonUpdateFailedError,
)
from src.modules.values.hierarchy.models import ValuesHierarchy
from src.modules.balances.models import Balance
from src.modules.balances_business_entities.models import BalanceBusinessEntity
from src.modules.comparison_values.models import ComparisonValue
from src.modules.comparison_values.meta.models import MetaComparisonValue
from src.domain.hooks.value_with_comparison import (
    on_value_with_comparison_updated,
    trigger_value_with_comparison_updated,
)


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
        saved_value = await self.ValuesService._create_value_with_meta(data.value, db=db)

        if data.comparison_value.value_from is None:
            data.comparison_value.value_from = saved_value.id

        saved_comparison = await self.ComparisonValuesService._create_comparison(
            data.comparison_value, db=db
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

        return (
            RSValueWithComparison(
                value=saved_value,
                comparison_value=saved_comparison,
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
        updated_value = await self.ValuesService._update_value_with_meta(
            id, data.value, db=db
        )

        stmt = select(ComparisonValue).where(
            ComparisonValue.value_from == updated_value.id
        )
        result = await db.execute(stmt)
        existing_comparison = result.scalars().first()

        if existing_comparison:
            if data.comparison_value.value_from is None:
                data.comparison_value.value_from = updated_value.id
            updated_comparison = (
                await self.ComparisonValuesService._update_comparison(
                    existing_comparison.uid, data.comparison_value, db=db
                )
            )
        else:
            if data.comparison_value.value_from is None:
                data.comparison_value.value_from = updated_value.id
            updated_comparison = (
                await self.ComparisonValuesService._create_comparison(
                    data.comparison_value, db=db
                )
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

        return (
            RSValueWithComparison(
                value=updated_value,
                comparison_value=updated_comparison,
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
    Background hook that propagates a price/comparison change DOWNWARD through
    the hierarchy when a value's comparison is updated.

    Any descendant flagged with ``REACTIVE_UPDATE=1`` in its comparison meta will
    have its comparison recalculated from the aggregated values of all its parents.
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

    updated_value_id = rs_data.value.id

    async with SessionAsync() as db:
        await _update_children_recursively(updated_value_id, db=db)
        await db.commit()


async def _compute_comparison_update(
    parent_comparisons: Sequence[ComparisonValue],
    child_comparison: ComparisonValue,
) -> dict:
    """
    Pure computation step: derive the new comparison fields for a reactive child
    from its parents' current comparison values.

    Default strategy — sum all parent ``quantity_to`` values so that the child's
    cost equals the total cost of its components (e.g. arroz + agua + gas → arroz
    cocido).

    Extensibility:
        When ``DECORATORS_QUANTITY`` is present in the child comparison's meta it
        will define a JSON-schema pipeline that transforms the raw aggregated value
        before it is persisted.  Possible decorators: taxes, profit margin,
        marginal costs, etc.  Example meta field::

            {
                "DECORATORS_QUANTITY": [
                    {"type": "tax",    "rate": 0.16},
                    {"type": "margin", "rate": 0.20}
                ]
            }

    Args:
        parent_comparisons: All ``ComparisonValue`` rows whose ``value_from`` is a
                            direct parent of the reactive child.
        child_comparison:   The child's own ``ComparisonValue`` (available for
                            context / future decorator pipeline).

    Returns:
        A ``{field: new_value}`` dict ready to be applied via ``setattr``.
    """
    total_quantity_to = sum((comp.quantity_to or 0) for comp in parent_comparisons)

    # TODO: apply DECORATORS_QUANTITY pipeline from child comparison meta
    # meta_decorators = child_meta.get("DECORATORS_QUANTITY")
    # if meta_decorators:
    #     total_quantity_to = run_decorators_pipeline(total_quantity_to, meta_decorators)

    return {"quantity_to": total_quantity_to}


@injectable
async def _update_children_recursively(
    updated_value_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Traverse the hierarchy DOWNWARD from ``updated_value_id``.

    For every direct child:
    - If the child's comparison meta contains ``REACTIVE_UPDATE=1``:
        1. Fetch *all* of that child's parent comparisons (not just the one that
           triggered the update, since the child may depend on several parents).
        2. Delegate the calculation to ``_compute_comparison_update``.
        3. Persist the result.
    - Recurse into the child's own subtree regardless of its reactive flag, so
      that deeper reactive descendants are also updated.
    """
    # Direct children of the updated value
    stmt = select(ValuesHierarchy.ref_value_bottom).where(
        ValuesHierarchy.ref_value_top == updated_value_id
    )
    res = await db.execute(stmt)
    child_ids = res.scalars().all()

    for child_id in child_ids:
        # Fetch the child's own comparison value
        comp_stmt = select(ComparisonValue).where(
            ComparisonValue.value_from == child_id
        )
        comp_res = await db.execute(comp_stmt)
        child_comp = comp_res.scalars().first()

        if child_comp:
            # Check for REACTIVE_UPDATE=1 in the child's comparison meta
            meta_stmt = select(MetaComparisonValue).where(
                MetaComparisonValue.ref_comparison_value == child_comp.id,
                MetaComparisonValue.key == "REACTIVE_UPDATE",
                MetaComparisonValue.value == "1",
            )
            meta_res = await db.execute(meta_stmt)
            is_reactive = meta_res.scalars().first() is not None

            if is_reactive:
                # Gather ALL parent IDs of this reactive child (not just the
                # one that changed – the child aggregates all of them).
                all_parents_stmt = select(ValuesHierarchy.ref_value_top).where(
                    ValuesHierarchy.ref_value_bottom == child_id
                )
                all_parents_res = await db.execute(all_parents_stmt)
                all_parent_ids = all_parents_res.scalars().all()

                # Fetch the current comparison for every parent
                parent_comps_stmt = select(ComparisonValue).where(
                    ComparisonValue.value_from.in_(all_parent_ids)
                )
                parent_comps_res = await db.execute(parent_comps_stmt)
                parent_comps = parent_comps_res.scalars().all()

                # Compute and apply updated comparison fields
                updates = await _compute_comparison_update(parent_comps, child_comp)
                for field, new_value in updates.items():
                    setattr(child_comp, field, new_value)

                db.add(child_comp)
                await db.flush()

        # Always recurse — deeper descendants may be reactive even if this
        # child is not.
        await _update_children_recursively(child_id, db=db)
