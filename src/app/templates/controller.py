from fastapi import Request
from fastapi.responses import HTMLResponse
from core.types.ui.templates import ABCTemplate


class Template(ABCTemplate):
    
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