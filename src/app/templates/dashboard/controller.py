from fastapi import Request
from fastapi.responses import HTMLResponse
from core.utils.fastapi.fastapi_class import fastapi_class


fc = fastapi_class()
class Controller(fc.Base):
    
    @fc.router.get("/", response_class=HTMLResponse)
    async def main_dashboard(self, request: "Request"):
        return self.templates.TemplateResponse(
            request,
            name="pages/index.html",
            context={
                "request": request,
            },
        )
