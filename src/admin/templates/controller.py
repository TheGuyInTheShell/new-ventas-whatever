from fastapi import Request
from fastapi.responses import HTMLResponse
from core.lib.decorators import Get
from core.lib.register import Template

class Index(Template):

    @Get("/", response_class=HTMLResponse)
    async def main_dashboard(self, request: Request):
        return self.templates.TemplateResponse(
            request,
            name="pages/dashboard.html",
            context={
                "request": request,
            },
        )