from fastapi import Request
from fastapi.responses import HTMLResponse
from core.utils.fastapi.fastapi_class import fastapi_class


view = fastapi_class()
class Controller(view.Base):
    
    @view.router.get("/", response_class=HTMLResponse)
    async def main_dashboard(self, request: "Request"):
        return self.templates.TemplateResponse(
            request,
            name="pages/index.html",
            context={
                "request": request,
            },
        )
    