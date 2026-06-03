import math
from typing import Any, Tuple, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import SessionAsync
from src.modules.balances.models import Balance
from src.modules.balances.decorators.models import BalanceDecorator
from src.domain.hooks.balances import on_balance_updated
from src.modules.balances.schemas import RSBalance


def apply_decorators(base_value: float, decorators_list: Optional[list[dict]]) -> float:
    """
    Evaluates a sequence of custom decorator operations on a base value.
    Supports operations: 'percentage', 'addition', 'subtraction', 'multiplication'.
    """
    current = base_value
    for dec in decorators_list or []:
        dec_type = dec.get("type")
        dec_qty = 0.0
        try:
            dec_qty = float(dec.get("quantity", 0.0))
        except (ValueError, TypeError):
            pass

        if dec_type == "percentage":
            current = current + (current * (dec_qty / 100.0))
        elif dec_type == "addition":
            current = current + dec_qty
        elif dec_type == "subtraction":
            current = current - dec_qty
        elif dec_type == "multiplication":
            current = current * dec_qty
    return current


@on_balance_updated
async def recursive_hierarchy_balance_update(
    result: Tuple[RSBalance, Any] | RSBalance, *args, **kwargs
):
    """
    Background hook that propagates a balance change DOWNWARD through
    the hierarchy when a balance is updated.
    """
    rs_data = None
    if isinstance(result, tuple) and len(result) == 2:
        val, err = result
        if not err and val:
            rs_data = val
    elif isinstance(result, RSBalance):
        rs_data = result

    if not rs_data:
        return

    updated_balance_id = rs_data.id

    async with SessionAsync() as db:
        await _update_children_recursively(updated_balance_id, db=db)
        await db.commit()


async def _update_children_recursively(parent_balance_id: int, db: AsyncSession):
    """
    Recursively update target balances that are linked via a reactive decorator.
    """
    # Find all decorators where this balance is the source, and it is reactive
    stmt = select(BalanceDecorator).where(
        BalanceDecorator.ref_balance_from == parent_balance_id,
        BalanceDecorator.is_reactive == True
    )
    result = await db.execute(stmt)
    decorators = result.scalars().all()

    for decorator in decorators:
        child_id = decorator.ref_balance_to
        
        # Calculate new quantity for the child: BOM / Limiting Reagent Logic
        parents_stmt = select(Balance, BalanceDecorator).join(
            BalanceDecorator,
            BalanceDecorator.ref_balance_from == Balance.id
        ).where(
            BalanceDecorator.ref_balance_to == child_id,
            BalanceDecorator.is_reactive == True
        )
        parents_result = await db.execute(parents_stmt)
        parents_and_decorators = parents_result.all()

        possible_yields = []
        for p_balance, p_decorator in parents_and_decorators:
            ratio = 1.0
            decorators_list = []
            if p_decorator.balance_decorators and isinstance(p_decorator.balance_decorators, dict):
                ratio = float(p_decorator.balance_decorators.get("required_quantity_per_unit", 1.0))
                decorators_list = p_decorator.balance_decorators.get("decorators", [])
            
            if ratio <= 0:
                ratio = 1.0 # Prevent division by zero
                
            # Apply decorators to the base parent quantity before dividing by ratio
            decorated_parent_qty = apply_decorators(p_balance.quantity, decorators_list)
            max_yield = decorated_parent_qty / ratio
            possible_yields.append(max_yield)

        new_quantity = 0.0
        if possible_yields:
            new_quantity = float(math.floor(min(possible_yields)))

        # Update the child balance
        child_stmt = select(Balance).where(Balance.id == child_id)
        child_result = await db.execute(child_stmt)
        child_balance = child_result.scalar_one()

        if child_balance.quantity != new_quantity:
            child_balance.quantity = new_quantity
            # Since the child updated, we need to propagate its changes to its own children
            await _update_children_recursively(child_id, db)
