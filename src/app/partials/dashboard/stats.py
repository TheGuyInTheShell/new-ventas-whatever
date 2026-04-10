from fastapi import Request
from fastapi.responses import HTMLResponse
from core.lib.decorators import Get
from core.lib.register import Partial

class StatsPartial(Partial):
    """Controlador de parciales para el dashboard."""

    @Get("/", response_class=HTMLResponse)
    async def refresh_stats(self, request: Request) -> HTMLResponse:
        """Retorna el fragmento HTML del grid de estadísticas.
        
        Útil para actualizaciones vía HTMX.
        """
        return self.templates.TemplateResponse(
            request,
            name="components/dashboard/stats_grid.html",
            context={"request": request}
        )
