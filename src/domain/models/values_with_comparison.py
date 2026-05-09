from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, List

from src.modules.values.models import Value
from src.modules.comparison_values.models import ComparisonValue
from src.modules.values.hierarchy.models import ValuesHierarchy
from src.domain.schemas.values_with_comparison import (
    QueryValuesWithComparison,
    ResultValueWithComparison,
    RSValueWithHierarchy,
)


class BuilderValueWithComparison:
    def __init__(self, db: AsyncSession):
        self.db = db
        # Base query joining Value and ComparisonValue
        self.stmt = select(Value, ComparisonValue)
        self.query_params: Optional[QueryValuesWithComparison] = None

    def set_query(
        self, query: QueryValuesWithComparison
    ) -> "BuilderValueWithComparison":
        self.query_params = query
        return self

    def _apply_value_filters(self):
        if not self.query_params or not self.query_params.value:
            return

        vq = self.query_params.value
        if vq.id is not None:
            self.stmt = self.stmt.where(Value.id == vq.id)
        if vq.name is not None:
            self.stmt = self.stmt.where(Value.name.ilike(f"%{vq.name}%"))
        if vq.expression is not None:
            self.stmt = self.stmt.where(Value.expression == vq.expression)
        # type and context removed from QueryValue
        if vq.identifier is not None:
            self.stmt = self.stmt.where(Value.identifier == vq.identifier)
        if vq.type is not None:
            self.stmt = self.stmt.where(Value.type == vq.type)

        # Handle soft deletes
        self.stmt = self.stmt.where(Value.is_deleted == False)

    def _apply_comparison_filters(self):
        if not self.query_params or not self.query_params.comparison_value:
            return

        cq = self.query_params.comparison_value
        if cq.quantity_from is not None:
            self.stmt = self.stmt.where(
                ComparisonValue.quantity_from == cq.quantity_from
            )
        if cq.quantity_to is not None:
            self.stmt = self.stmt.where(ComparisonValue.quantity_to == cq.quantity_to)
        if cq.value_from is not None:
            self.stmt = self.stmt.where(ComparisonValue.value_from == cq.value_from)
        if cq.value_to is not None:
            self.stmt = self.stmt.where(ComparisonValue.value_to == cq.value_to)
        if cq.ref_business_entity is not None:
            self.stmt = self.stmt.where(
                ComparisonValue.ref_business_entity == cq.ref_business_entity
            )

        self.stmt = self.stmt.where(ComparisonValue.is_deleted == False)

    def _apply_business_entity_filter(self):
        if self.query_params and self.query_params.ref_business_entity is not None:
            eb_id = self.query_params.ref_business_entity
            # Ensure both Value and ComparisonValue (if present) are filtered by the business entity
            self.stmt = self.stmt.where(Value.ref_business_entity == eb_id)
            # If there's a join with ComparisonValue, we also filter it if it's not null (since it's an outer join in some cases)
            self.stmt = self.stmt.where(
                (ComparisonValue.ref_business_entity == eb_id)
                | (ComparisonValue.id == None)
            )

    def _apply_eager_loading(self):
        # Balances are critical for inventory, so we load them by default now
        self.stmt = self.stmt.options(selectinload(Value.balances))

        if not self.query_params:
            return

        if self.query_params.value and self.query_params.value.full_meta:
            self.stmt = self.stmt.options(selectinload(Value.meta))

        if (
            self.query_params.comparison_value
            and self.query_params.comparison_value.full_meta
        ):
            self.stmt = self.stmt.options(selectinload(ComparisonValue.meta))

    def _apply_join(self):
        if not self.query_params:
            return

        if not self.query_params.value and not self.query_params.comparison_value:
            return

        has_v = getattr(self.query_params.value, "id", None) is not None
        has_c = getattr(self.query_params.comparison_value, "id", None) is not None

        has_v_id = has_v if has_v else None
        has_c_v_from = has_c if has_c else None

        match (has_v, has_c):
            case (False, True):
                # We want ComparisonValue and its source Value (to satisfy the return format)
                self.stmt = select(Value, ComparisonValue).join(
                    Value, Value.id == ComparisonValue.value_from, isouter=True
                )
            case (True, True) if has_v_id == has_c_v_from:
                # Exact match between Value and ComparisonValue
                self.stmt = select(Value, ComparisonValue).join(
                    ComparisonValue, Value.id == ComparisonValue.value_from
                )
            case _:
                # Default fallback: Value with optional ComparisonValues
                self.stmt = select(Value, ComparisonValue).join(
                    ComparisonValue,
                    Value.id == ComparisonValue.value_from,
                    isouter=True,
                )

    def _apply_hierarchy_filter(self):
        """If ref_super_values_ids is given, restrict results to values that are children of those parents."""
        if not self.query_params or not self.query_params.ref_super_values_ids:
            return
        self.stmt = self.stmt.join(
            ValuesHierarchy, ValuesHierarchy.ref_value_bottom == Value.id
        ).where(
            ValuesHierarchy.ref_value_top.in_(self.query_params.ref_super_values_ids)
        )

    def build(self) -> "BuilderValueWithComparison":
        self._apply_join()
        self._apply_value_filters()
        self._apply_comparison_filters()
        self._apply_business_entity_filter()
        self._apply_hierarchy_filter()
        self._apply_eager_loading()
        return self

    async def execute(self) -> ResultValueWithComparison:
        from sqlalchemy.orm.attributes import instance_state
        from src.modules.values.schemas import RSMetaValue
        from src.modules.comparison_values.schemas import (
            RSComparisonValue,
            RSComparisonValueSimple,
        )

        result = await self.db.execute(self.stmt)
        rows = result.unique().all()

        values = []
        comparisons = []

        # Collect all value IDs so we can batch-load hierarchy parents
        seen_values: dict[int, RSValueWithHierarchy] = {}
        seen_comparisons = set()

        for value_obj, comp_obj in rows:
            if value_obj and value_obj.id not in seen_values:
                unloaded = instance_state(value_obj).unloaded

                meta_list = None
                if "meta" not in unloaded:
                    meta_list = []
                    for m in getattr(value_obj, "meta", []):
                        meta_list.append(
                            RSMetaValue(key=m.key, value=m.value)
                        )

                balance_list = None
                if "balances" not in unloaded:
                    balance_list = []
                    from src.modules.values.schemas import RSBalance

                    for b in getattr(value_obj, "balances", []):
                        balance_list.append(
                            RSBalance(id=b.id, quantity=b.quantity, type=b.type)
                        )

                rv = RSValueWithHierarchy(
                    uid=value_obj.uid,
                    id=value_obj.id,
                    name=value_obj.name,
                    expression=value_obj.expression,
                    type=value_obj.type,
                    ref_business_entity=value_obj.ref_business_entity,
                    identifier=value_obj.identifier,
                    meta=meta_list,
                    balances=balance_list,
                    ref_super_values_ids=[],
                )
                seen_values[value_obj.id] = rv
                values.append(rv)

            if comp_obj and comp_obj.id not in seen_comparisons:
                unloaded_c = instance_state(comp_obj).unloaded

                sv = None
                if "source_value" not in unloaded_c and comp_obj.source_value:
                    sv = RSComparisonValueSimple(
                        id=comp_obj.source_value.id,
                        uid=comp_obj.source_value.uid,
                        name=comp_obj.source_value.name,
                        expression=comp_obj.source_value.expression,
                    )

                tv = None
                if "target_value" not in unloaded_c and comp_obj.target_value:
                    tv = RSComparisonValueSimple(
                        id=comp_obj.target_value.id,
                        uid=comp_obj.target_value.uid,
                        name=comp_obj.target_value.name,
                        expression=comp_obj.target_value.expression,
                    )

                comparisons.append(
                    RSComparisonValue(
                        uid=comp_obj.uid,
                        id=comp_obj.id,
                        quantity_from=comp_obj.quantity_from,
                        quantity_to=comp_obj.quantity_to,
                        value_from=comp_obj.value_from,
                        value_to=comp_obj.value_to,
                        ref_business_entity=comp_obj.ref_business_entity,
                        source_value=sv,
                        target_value=tv,
                    )
                )
                seen_comparisons.add(comp_obj.id)

        # Batch-load parent hierarchy IDs for the returned values
        if seen_values:
            hier_stmt = select(ValuesHierarchy).where(
                ValuesHierarchy.ref_value_bottom.in_(seen_values.keys())
            )
            hier_result = await self.db.execute(hier_stmt)
            for h in hier_result.scalars().all():
                if h.ref_value_bottom in seen_values:
                    seen_values[h.ref_value_bottom].ref_super_values_ids.append(
                        h.ref_value_top
                    )

        return ResultValueWithComparison(
            value=values if values else None,
            comparison_value=comparisons if comparisons else None,
        )
