from core.lib.decorators import Post, Put
from core.lib.register import Controller
from core.security.shield import Shield
from core.lib.decorators.services import Services

from src.modules.d.schemas.transaction_and_invoice import RQAdjustBalance, InvoiceSales
from src.modules.d.services.transaction_and_invoice import DTransactionAndInvoiceService
from core.lib.http.errors import error_response


@Shield.register(context="Transaction and Invoice API")
@Services(DTransactionAndInvoiceService)
class TransactionAndInvoiceController(Controller):
    DTransactionAndInvoiceService: DTransactionAndInvoiceService

    @Post("/")
    @Shield.need(
        name="create.transaction_and_invoice",
        action="create",
        type="endpoint",
        description="Create an invoice and transactions.",
    )
    async def create_invoice(self, payload: InvoiceSales):
        result, error = (
            await self.DTransactionAndInvoiceService.create_transaction_and_invoice_service(
                payload
            )
        )
        if error:
            return error_response(error)
        return result

    @Put("/adjust")
    @Shield.need(
        name="adjust.transaction_and_invoice",
        action="update",
        type="endpoint",
        description="Adjust the stock quantity of an inventory balance.",
    )
    async def adjust_stock(self, payload: RQAdjustBalance):
        result, error = (
            await self.DTransactionAndInvoiceService.adjust_transaction_and_invoice_service(
                payload
            )
        )
        if error:
            return error_response(error)
        return result
