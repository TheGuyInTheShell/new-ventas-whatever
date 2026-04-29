from sqlalchemy import ForeignKey, Integer, String, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING

from core.database import BasicBaseAsync

if TYPE_CHECKING:
    from src.modules.comparison_values.models import ComparisonValue
    from src.modules.values.meta.models import MetaValue
    from src.modules.balances.models import Balance
    from src.modules.values.schemas import RQValueQuery
    from sqlalchemy.ext.asyncio import AsyncSession
    from src.modules.business_entities.models import BusinessEntity


class Value(BasicBaseAsync):
    """
    Represents a unit of value that can be compared with other values.
    Examples: Dollar (USD), Bitcoin (BTC), Hummer H2 (CAR) (Vehicle) 2016, etc.
    """

    __tablename__ = "values"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    ref_business_entity: Mapped[int] = mapped_column(Integer, ForeignKey("business_entities.id", ondelete="CASCADE"), nullable=False)
    expression: Mapped[str] = mapped_column(String(50), nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    identifier: Mapped[str] = mapped_column(String(100), nullable=True)

    # Relationships
    comparisons_from: Mapped[List["ComparisonValue"]] = relationship(
        "ComparisonValue",
        foreign_keys="[ComparisonValue.value_from]",
        back_populates="source_value",
        cascade="all, delete-orphan",
    )
    comparisons_to: Mapped[List["ComparisonValue"]] = relationship(
        "ComparisonValue",
        foreign_keys="[ComparisonValue.value_to]",
        back_populates="target_value",
        cascade="all, delete-orphan",
    )

    meta: Mapped[List["MetaValue"]] = relationship(
        "MetaValue",
        back_populates="value_obj",
        cascade="all, delete-orphan",
    )

    balances: Mapped[List["Balance"]] = relationship(
        "Balance",
        back_populates="value",
        cascade="all, delete-orphan",
    )

    business_entity: Mapped["BusinessEntity"] = relationship("BusinessEntity")

    __table_args__ = (
        Index("ix_values_ref_business_entity_active", "ref_business_entity"),
        Index("ix_values_name_ref_business_entity", "name", "ref_business_entity"),
        Index("ix_values_name_type", "name", "type"),
        Index("ix_values_name_ref_business_entity_type", "name", "ref_business_entity", "type"),
        UniqueConstraint(
            "name", "ref_business_entity", "type", name="uix_values_name_ref_business_entity_type"
        ),
    )

    @classmethod
    async def query(cls, db: "AsyncSession", q: "RQValueQuery"):
        """
        Flexible query method that supports:
        - Filtering by name, expression, type, context, identifier
        - Soft-delete status filtering (exists / deleted / all)
        - Optional eager-loading of meta relationships
        - Optional JOIN with ComparisonValue (and its relationships)
        - Ordering by any allowed column, asc/desc
        - Pagination with page + page_size
        Returns (items: List[Value], total: int)
        """
        from sqlalchemy import select, func, desc as sa_desc
        from sqlalchemy.orm import selectinload
        from src.modules.comparison_values.models import ComparisonValue

        # ---- base query ----
        stmt = select(cls)

        # ---- status filter (soft delete) ----
        if q.status == "exists":
            stmt = stmt.where(cls.is_deleted == False)
        elif q.status == "deleted":
            stmt = stmt.where(cls.is_deleted == True)
        # "all" → no filter

        # ---- field filters (only applied when not None) ----
        if q.name is not None:
            stmt = stmt.where(cls.name.ilike(f"%{q.name}%"))
        if q.expression is not None:
            stmt = stmt.where(cls.expression == q.expression)
        if q.type is not None:
            stmt = stmt.where(cls.type == q.type)
        if q.ref_business_entity is not None:
            stmt = stmt.where(cls.ref_business_entity == q.ref_business_entity)
        if q.identifier is not None:
            stmt = stmt.where(cls.identifier == q.identifier)

        # ---- optional comparison join (for filtering) ----
        if q.comparison or q.comparison_to_id is not None:
            # If comparison_to_id is provided, only return values that have a comparison to that ID
            if q.comparison_to_id is not None:
                stmt = stmt.join(
                    ComparisonValue,
                    (cls.id == ComparisonValue.value_from)
                    & (ComparisonValue.value_to == q.comparison_to_id)
                    & (ComparisonValue.is_deleted == False),
                )
            else:
                stmt = stmt.join(ComparisonValue, cls.id == ComparisonValue.value_from)

        # ---- count (before options & pagination) ----
        # Use subquery to correctly count rows with joins/filters
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar() or 0

        # ---- eager-loads (applied after count) ----
        if q.comparison or q.comparison_to_id is not None:
            # eager-load properties accessed in comparison_to_response
            # If a specific target is requested, only load that comparison
            if q.comparison_to_id is not None:
                comp_loader = selectinload(
                    cls.comparisons_from.and_(
                        ComparisonValue.value_to == q.comparison_to_id,
                        ComparisonValue.is_deleted == False,
                    )
                )
            else:
                comp_loader = selectinload(cls.comparisons_from)

            stmt = stmt.options(
                comp_loader.selectinload(ComparisonValue.source_value),
                comp_loader.selectinload(ComparisonValue.target_value),
            )
            if q.comparison_meta:
                stmt = stmt.options(comp_loader.selectinload(ComparisonValue.meta))

        if q.meta:
            stmt = stmt.options(selectinload(cls.meta))

        if q.balances:
            stmt = stmt.options(selectinload(cls.balances))

        # ---- ordering ----
        order_col = getattr(cls, q.order_by if q.order_by != "context" else "ref_business_entity", cls.name)
        if q.order == "desc":
            stmt = stmt.order_by(sa_desc(order_col))
        else:
            stmt = stmt.order_by(order_col.asc())

        # ---- pagination ----
        page = max(q.page, 1)
        # Ensure page_size is valid
        page_size = q.page_size if q.page_size > 0 else 10
        offset = (page - 1) * page_size
        stmt = stmt.limit(page_size).offset(offset)

        # ---- execute ----
        result = await db.execute(stmt)
        items = result.scalars().unique().all()

        # ---- post-load balance type filter ----
        # Filter in Python to avoid unreliable ORM selectinload.and_() syntax
        if q.balances and getattr(q, "balance_type", None):
            for item in items:
                if item.balances is not None:
                    item.balances = [
                        b for b in item.balances if b.type == q.balance_type
                    ]

        return list(items), int(total)
