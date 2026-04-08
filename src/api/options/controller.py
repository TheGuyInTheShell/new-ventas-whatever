from typing import Dict

from core.lib.decorators import Post, Get, Services
from core.lib.register import Controller
from src.modules.options.services import OptionsService
from src.modules.options.schemas import Option

@Services(OptionsService)
class OptionsController(Controller):
    OptionsService: "OptionsService"

    @Post("/")
    async def create_option(self, name: str, context: str, value: str) -> Option:
        return await self.OptionsService.create_options(name, context, value)

    @Get("/")
    async def get_options(self) -> Dict[str, str]:

        return {
            "ping": "pong",
        }