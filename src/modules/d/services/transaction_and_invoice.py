from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import HTTPException
from typing import TYPE_CHECKING
import json
from core.lib.register.service import Service

# Shared float precision for all inventory/balance quantities

from app.context.globals import _round_quantity
from ...balances.models import Balance
from ..schemas.transaction_and_invoice import RQAdjustBalance
from ...invoices.models import Invoice
from ...transactions.models import Transaction
from ...invoice_transactions.models import InvoiceTransaction
from ...invoice_business_entities.models import InvoiceBusinessEntity

from ...comparison_values.historical.models import ComparisonValueHistorical
from ...balances_business_entities.models import BalanceBusinessEntity
from ..schemas.transaction_and_invoice import InvoiceSales

class DTransactionAndInvoiceService(Service):
    async def create_transaction_and_invoice_service(self, db: AsyncSession, data: InvoiceSales) -> dict:
        """
        Full sales flow: resolve balances -> create historical comparison -> create transaction -> create invoice -> link all.
        """
        try:
            # 1. Create the Invoice
            invoice = Invoice(
                context=data.context or "sales",
                name=data.name or "Sale Invoice",
                type=data.type or "sale",
                serial=data.serial,
                notes=data.notes
            )
            db.add(invoice)
            await db.flush() # get invoice.id

            # 2. Link Invoice to Business Entity
            db.add(InvoiceBusinessEntity(ref_invoice=invoice.id, ref_business_entity=data.business_entity_id))

            created_transactions = []

            # 3. Process each transaction
            for tx_data in data.transactions:
                # Resolve balances if not provided
                balance_from_id = tx_data.ref_balance_from
                balance_to_id = tx_data.ref_balance_to

                if not balance_from_id:
                    balance_from_id = await self._resolve_balance(db, tx_data.ref_value_from, data.business_entity_id)
                if not balance_to_id:
                    balance_to_id = await self._resolve_balance(db, tx_data.ref_value_to, data.business_entity_id)

                # Resolve/Create Historical Comparison if needed
                historical_id = tx_data.ref_comparation_values_historical
                if not historical_id:
                    # Create a snapshot
                    historical = ComparisonValueHistorical(
                        context=data.context or "sales_snapshot",
                        quantity_from=1, # Default base
                        quantity_to=tx_data.quantity, # Using quantity as current rate/qty
                        value_from=tx_data.ref_value_from,
                        value_to=tx_data.ref_value_to
                    )
                    db.add(historical)
                    await db.flush()
                    historical_id = historical.id

                # Create Transaction
                transaction = Transaction(
                    quantity=str(tx_data.quantity),
                    quantity_to="0", # Default or derived?
                    operation_type=tx_data.operation_type,
                    reference_code=tx_data.reference_code,
                    ref_by_user=1, # Proxy user
                    ref_balance_from=balance_from_id,
                    ref_balance_to=balance_to_id
                )
                db.add(transaction)
                await db.flush()

                # Link Invoice -> Transaction
                db.add(InvoiceTransaction(ref_invoice=invoice.id, ref_transaction=transaction.id))
                
                created_transactions.append(transaction.id)

            await db.commit()

            return {
                "success": True,
                "invoice_id": invoice.id,
                "transaction_ids": created_transactions
            }

        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    async def _resolve_balance(self, db: AsyncSession, value_id: int, entity_id: int) -> int:
        """Helper to find a balance for a value and business entity."""
        stmt = select(Balance.id).join(BalanceBusinessEntity).where(
            Balance.ref_value == value_id,
            BalanceBusinessEntity.ref_business_entity == entity_id
        )
        result = await db.execute(stmt)
        balance_id = result.scalars().first()
        
        if not balance_id:
            # Fallback: find any balance for this value if not specifically linked to the entity?
            # Or create one? Requirements are a bit fuzzy here, let's try to find any first.
            stmt_any = select(Balance.id).where(Balance.ref_value == value_id)
            result_any = await db.execute(stmt_any)
            balance_id = result_any.scalars().first()
            
        if not balance_id:
            raise HTTPException(status_code=404, detail=f"No balance found for value_id {value_id}")
            
        return balance_id

    async def adjust_transaction_and_invoice_service(self, db: AsyncSession, data: RQAdjustBalance) -> dict:
        """
        Adjust the stock (quantity) of an inventory Balance.
        If 'is_adjustment' is true, generate an Invoice and pseudo-Transaction for history.
        """
        try:
            # 1. Fetch the Balance
            stmt = select(Balance).where(Balance.id == data.balance_id)
            result = await db.execute(stmt)
            balance = result.scalars().first()
            
            if not balance:
                raise HTTPException(status_code=404, detail="Inventory Balance not found for the given value.")

            if not data.is_adjustment:
                # Direct edit
                balance.quantity = data.new_quantity
            else:
                # ----------------------------------------------------------------
                # STEP 0: Calculate the delta (how much are we adjusting by?)
                # ----------------------------------------------------------------
                # Round to avoid float precision ghosts like 20.03 - 20.0 = 0.030000000000001422
                delta = _round_quantity(data.new_quantity - balance.quantity)
                
                if delta != 0:
                    # ------------------------------------------------------------
                    # STEP 1: Find the adjustment balance scoped to the same
                    # business entities as the source balance.
                    #
                    # We look for an existing Balance of type "adjustment" for
                    # the same value that is ALSO linked (via BalanceBusinessEntity)
                    # to at least one of the same entities as the source balance.
                    # This ensures we never mix up adjustment records across entities.
                    # ------------------------------------------------------------

                    # First, resolve which business entities the source balance belongs to.
                    stmt_src_entities = select(BalanceBusinessEntity.ref_business_entity).where(
                        BalanceBusinessEntity.ref_balance == balance.id
                    )
                    result_src_entities = await db.execute(stmt_src_entities)
                    src_entity_ids = result_src_entities.scalars().all()
                    # src_entity_ids might be empty if the balance has no entity link yet.

                    adj_balance = None

                    if src_entity_ids:
                        # Look for an adjustment balance for this value that is already
                        # linked to the same set of business entities.
                        stmt_adj = (
                            select(Balance)
                            .join(
                                BalanceBusinessEntity,
                                BalanceBusinessEntity.ref_balance == Balance.id
                            )
                            .where(
                                Balance.ref_value == balance.ref_value,
                                Balance.type == "adjustment",
                                BalanceBusinessEntity.ref_business_entity.in_(src_entity_ids)
                            )
                            .limit(1)
                        )
                        result_adj = await db.execute(stmt_adj)
                        adj_balance = result_adj.scalars().first()
                    else:
                        # No entity links on source balance — fall back to a simple
                        # lookup by value (old behaviour, just in case).
                        stmt_adj = select(Balance).where(
                            Balance.ref_value == balance.ref_value,
                            Balance.type == "adjustment",
                        ).limit(1)
                        result_adj = await db.execute(stmt_adj)
                        adj_balance = result_adj.scalars().first()

                    # ------------------------------------------------------------
                    # STEP 2: Create the adjustment balance if it does not exist yet.
                    # ------------------------------------------------------------
                    if not adj_balance:
                        adj_balance = Balance(
                            type="adjustment",
                            quantity=0.0,
                            ref_value=balance.ref_value
                        )
                        db.add(adj_balance)
                        await db.flush()  # flush to get adj_balance.id before inserting pivots

                    # ------------------------------------------------------------
                    # STEP 3 (optional): Link adj_balance to the same business
                    # entities as the source balance, but SKIP any that already exist.
                    # ------------------------------------------------------------
                    for ent_id in src_entity_ids:
                        # Check whether this specific pivot row already exists.
                        stmt_exists = select(BalanceBusinessEntity).where(
                            BalanceBusinessEntity.ref_balance == adj_balance.id,
                            BalanceBusinessEntity.ref_business_entity == ent_id
                        )
                        result_exists = await db.execute(stmt_exists)
                        already_linked = result_exists.scalars().first()
                        
                        if not already_linked:
                            db.add(BalanceBusinessEntity(
                                ref_balance=adj_balance.id,
                                ref_business_entity=ent_id
                            ))

                    # ------------------------------------------------------------
                    # STEP 4: Create an Invoice + Transaction for the audit trail.
                    # Every adjustment produces a trackable document pair.
                    # ------------------------------------------------------------
                    invoice = Invoice(
                        context="chinese_restaurant",
                        name="Inventory Adjustment",
                        type="adjustment",
                        notes=data.notes or f"Manual adjustment of {abs(delta)} units."
                    )
                    db.add(invoice)
                    await db.flush()  # get invoice.id

                    # direction: who's giving and who's receiving?
                    # delta > 0  → main balance goes up   → adj_balance gives  (+)
                    # delta < 0  → main balance goes down  → adj_balance receives (-)
                    operation_type = "+" if delta > 0 else "-"
                    transaction = Transaction(
                        quantity=str(abs(delta)),
                        quantity_to="0",
                        operation_type=operation_type,
                        ref_by_user=1,  # system proxy user
                        ref_balance_from=adj_balance.id if delta > 0 else balance.id,
                        ref_balance_to=balance.id if delta > 0 else adj_balance.id,
                    )
                    db.add(transaction)
                    await db.flush()

                    # Link the invoice to the transaction.
                    db.add(InvoiceTransaction(ref_invoice=invoice.id, ref_transaction=transaction.id))

                    # ------------------------------------------------------------
                    # STEP 5: Apply quantity changes to both balances.
                    # The adj_balance acts as a running counter of manual corrections:
                    #   • adj_balance.quantity -= delta
                    #     (if we added 10 to stock, adj_balance decreases by 10)
                    #     (if we removed 5 from stock, adj_balance increases by 5)
                    # ------------------------------------------------------------
                    balance.quantity = _round_quantity(data.new_quantity)
                    adj_balance.quantity = _round_quantity(adj_balance.quantity - delta)
                
            await db.commit()
            await db.refresh(balance)
            
            return {
                "success": True,
                "balance_id": balance.id,
                "new_quantity": _round_quantity(balance.quantity)
            }

        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

