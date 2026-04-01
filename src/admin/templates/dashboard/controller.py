from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRouter
from fastapi_restful.cbv import cbv


router = APIRouter()
@cbv(router)
class Controller(fc.Base):
    
    @router.get("/", response_class=HTMLResponse)
    async def main_dashboard(self, request: "Request"):
        return self.templates.TemplateResponse(
            request,
            name="pages/index.html",
            context={
                "request": request,
            },
        )
