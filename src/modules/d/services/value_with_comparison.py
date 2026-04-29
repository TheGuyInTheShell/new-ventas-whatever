from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import HTTPException
from typing import Optional, TYPE_CHECKING, List, Tuple

from core.lib.register.service import Service
from core.lib.decorators.services import Services
from fastapi import Depends
from fastapi_injectable import injectable

from core.database import get_async_db

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

from ...values.hierarchy.models import ValuesHierarchy
from ...balances.models import Balance
from ...balances_business_entities.models import BalanceBusinessEntity
from ...comparison_values.models import ComparisonValue

if TYPE_CHECKING:
    from ...values.models import Value


@Services(ValuesService, ComparisonValuesService)
class DValueWithComparisonService(Service):
    ValuesService: ValuesService
    ComparisonValuesService: ComparisonValuesService

    @injectable
    async def save_value_with_comparison_service(
        self, data: RQValueWithComparison, db: AsyncSession = Depends(get_async_db)
    ) -> RSValueWithComparison:
        """
        Saves a value (and its meta data) and a comparison (and its meta data).
        The comparison automatically uses the newly created value as its source if not provided.
        Also handles optional linking to an inventory value and auto-creating balances.
        """
        try:
            saved_value = await self.ValuesService.create_value_with_meta(data.value)

            if data.comparison_value.value_from is None:
                data.comparison_value.value_from = saved_value.id

            saved_comparison = await self.ComparisonValuesService.create_comparison(
                data.comparison_value
            )

            # 1. Hierarchy: link to all superior values (composite parent links)
            for super_id in data.ref_super_values_ids or []:
                hierarchy = ValuesHierarchy(
                    ref_value_top=super_id, ref_value_bottom=saved_value.id
                )
                db.add(hierarchy)

            # 2. Balance: auto-create a balance for this value using the provided type
            if data.balance_type:
                new_balance = Balance(quantity=0, type=data.balance_type, ref_value=saved_value.id)
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

            return RSValueWithComparison(
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
            )
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    @injectable
    async def update_value_with_comparison_service(
        self,
        id: str,
        data: RQValueWithComparison,
        db: AsyncSession = Depends(get_async_db),
    ) -> RSValueWithComparison:
        """
        Updates a value and a comparison.
        Also syncs the optional inventory hierarchy and balance business entities.
        """
        try:
            # Assuming the value and comparison updates handle finding the record by id (uid)
            updated_value = await self.ValuesService.update_value_with_meta(
                id, data.value
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
                    await self.ComparisonValuesService.update_comparison(
                        existing_comparison.uid, data.comparison_value
                    )
                )
            else:
                if data.comparison_value.value_from is None:
                    data.comparison_value.value_from = updated_value.id
                updated_comparison = (
                    await self.ComparisonValuesService.create_comparison(
                        data.comparison_value
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
            await db.refresh(updated_value)
            await db.refresh(updated_comparison)

            return RSValueWithComparison(
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
            )

        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    @injectable
    async def get_values_with_comparison_service(
        self, data: QueryValuesWithComparison, db: AsyncSession = Depends(get_async_db)
    ) -> ResultValueWithComparison:
        """
        Query values and comparison values dynamically based on provided filters.
        """
        builder = BuilderValueWithComparison(db)
        result = await builder.set_query(data).build().execute()
        return result
