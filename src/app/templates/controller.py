from fastapi import Request
from fastapi.responses import HTMLResponse
from core.types.ui.templates import ViewFast


class Template(ViewFast):
    
    def add_pages(self):

        @self.router.get("", response_class=HTMLResponse)
        async def main_dashboard(request: Request):
            return self.templates.TemplateResponse(
                request,
                name="pages/dashboard.html",
                context={
                    "request": request,
                },
            )