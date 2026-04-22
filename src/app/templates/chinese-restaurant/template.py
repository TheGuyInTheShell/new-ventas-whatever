"""
Template controller para la sección de Restaurante Chino (/chinese-restaurant).
"""

from fastapi import Request
from fastapi.responses import HTMLResponse

from core.lib.decorators import Get, Services
from core.lib.register import Template
from core.services.ui.enqueue_js import enqueue_js, Site, Script
from core.services.ui.enqueue_css import enqueue_css, CssSite, Style
from core.security.shield import Shield

from src.modules.d.services.menu import MenuService


@Services(MenuService)
@Shield.register(context="ChineseRestaurant")
class ChineseRestaurant(Template):
    """Controlador de templates para el módulo de Restaurante Chino."""

    MenuService: "MenuService"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mock data for the demonstration
        self.mock_dishes = [
            {
                "id": 1,
                "name": "Spring Rolls",
                "price": 5.50,
                "currency": "$",
                "prep_time": "10 min",
                "image_id": "https://images.unsplash.com/photo-1544333346-64e4304856f7?w=400&h=400&fit=crop",
                "ingredients": [1, 2, 3],
            },
            {
                "id": 2,
                "name": "Egg Fried Rice",
                "price": 8.90,
                "currency": "$",
                "prep_time": "15 min",
                "image_id": "https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=400&h=400&fit=crop",
                "ingredients": [4, 5, 6],
            },
            {
                "id": 3,
                "name": "Kung Pao Chicken",
                "price": 12.50,
                "currency": "$",
                "prep_time": "20 min",
                "image_id": "https://images.unsplash.com/photo-1525755662778-989d0524087e?w=400&h=400&fit=crop",
                "ingredients": [7, 8, 9],
            },
            {
                "id": 4,
                "name": "Sweet and Sour Pork",
                "price": 11.00,
                "currency": "$",
                "prep_time": "18 min",
                "image_id": "https://images.unsplash.com/photo-1623653387945-2fd25214f8fc?w=400&h=400&fit=crop",
                "ingredients": [10, 11],
            },
            {
                "id": 5,
                "name": "Wonton Soup",
                "price": 6.50,
                "currency": "$",
                "prep_time": "12 min",
                "image_id": "https://images.unsplash.com/photo-1570197788417-0e93347c6a9b?w=400&h=400&fit=crop",
                "ingredients": [12, 13],
            },
            {
                "id": 6,
                "name": "Dim Sum Platter",
                "price": 15.00,
                "currency": "$",
                "prep_time": "25 min",
                "image_id": "https://images.unsplash.com/photo-1496116214483-b43419b517e3?w=400&h=400&fit=crop",
                "ingredients": [14, 15, 16],
            },
        ]

        self.mock_tables = [
            {"id": 1, "number": "T-01", "capacity": 2, "status": "Available"},
            {"id": 2, "number": "T-02", "capacity": 4, "status": "Occupied"},
            {"id": 3, "number": "T-03", "capacity": 4, "status": "Reserved"},
            {"id": 4, "number": "T-04", "capacity": 6, "status": "Available"},
            {"id": 5, "number": "V-01", "capacity": 8, "status": "Occupied"},
            {"id": 6, "number": "T-05", "capacity": 2, "status": "Available"},
        ]

        self.mock_staff = [
            {
                "id": 1,
                "name": "Li Wei",
                "role": "Head Chef",
                "status": "Active",
                "avatar": "https://i.pravatar.cc/150?u=liwei",
            },
            {
                "id": 2,
                "name": "Chen Xiao",
                "role": "Sous Chef",
                "status": "Active",
                "avatar": "https://i.pravatar.cc/150?u=chenxiao",
            },
            {
                "id": 3,
                "name": "Zhang San",
                "role": "Waiter",
                "status": "On Break",
                "avatar": "https://i.pravatar.cc/150?u=zhangsan",
            },
            {
                "id": 4,
                "name": "Wang Wu",
                "role": "Waiter",
                "status": "Active",
                "avatar": "https://i.pravatar.cc/150?u=wangwu",
            },
        ]

    async def _get_common_context(self, request: Request):
        return {
            "request": request,
            "menu": await self.MenuService.get_menu_component(request),
        }

    @Get("/menu", response_class=HTMLResponse)
    @Shield.need(name="chinese_restaurant.menu_page", action="read", type="template")
    @enqueue_css(Style(href="/app-static/css/app.css"))
    @enqueue_js(Script(src="/app-static/javascript/icons.js", type="module"))
    @enqueue_js(
        Script(src="/app-static/javascript/pages/chinese-restaurant/menu.js", type="module", defer=True),
        position=Site.HEAD,
    )
    @enqueue_js(
        Script(src="/app-static/javascript/index.js", type="module", defer=True),
        position=Site.BODY_AFTER,
    )
    async def menu_page(self, request: Request) -> HTMLResponse:
        context = await self._get_common_context(request)
        context.update({"dishes": self.mock_dishes})
        return self.templates.TemplateResponse(
            request, name="pages/chinese-restaurant/menu.html", context=context
        )

    @Get("/orders", response_class=HTMLResponse)
    @Shield.need(name="chinese_restaurant.orders_page", action="read", type="template")
    @enqueue_css(Style(href="/app-static/css/app.css"))
    @enqueue_js(Script(src="/app-static/javascript/icons.js", type="module"))
    @enqueue_js(
        Script(src="/app-static/javascript/pages/chinese-restaurant/orders.js", type="module", defer=True),
        position=Site.HEAD,
    )
    @enqueue_js(
        Script(src="/app-static/javascript/index.js", type="module", defer=True),
        position=Site.BODY_AFTER,
    )
    async def orders_page(self, request: Request) -> HTMLResponse:
        context = await self._get_common_context(request)
        context.update({"dishes": self.mock_dishes})
        return self.templates.TemplateResponse(
            request, name="pages/chinese-restaurant/orders.html", context=context
        )

    @Get("/tables", response_class=HTMLResponse)
    @Shield.need(name="chinese_restaurant.tables_page", action="read", type="template")
    @enqueue_css(Style(href="/app-static/css/app.css"))
    @enqueue_js(Script(src="/app-static/javascript/icons.js", type="module"))
    @enqueue_js(
        Script(src="/app-static/javascript/pages/chinese-restaurant/tables.js", type="module", defer=True),
        position=Site.HEAD,
    )
    @enqueue_js(
        Script(src="/app-static/javascript/index.js", type="module", defer=True),
        position=Site.BODY_AFTER,
    )
    async def tables_page(self, request: Request) -> HTMLResponse:
        context = await self._get_common_context(request)
        context.update({"tables": self.mock_tables})
        return self.templates.TemplateResponse(
            request, name="pages/chinese-restaurant/tables.html", context=context
        )

    @Get("/staff", response_class=HTMLResponse)
    @Shield.need(name="chinese_restaurant.staff_page", action="read", type="template")
    @enqueue_css(Style(href="/app-static/css/app.css"))
    @enqueue_js(Script(src="/app-static/javascript/icons.js", type="module"))
    @enqueue_js(
        Script(src="/app-static/javascript/pages/chinese-restaurant/staff.js", type="module", defer=True),
        position=Site.HEAD,
    )
    @enqueue_js(
        Script(src="/app-static/javascript/index.js", type="module", defer=True),
        position=Site.BODY_AFTER,
    )
    async def staff_page(self, request: Request) -> HTMLResponse:
        context = await self._get_common_context(request)
        context.update({"staff": self.mock_staff})
        return self.templates.TemplateResponse(
            request, name="pages/chinese-restaurant/staff.html", context=context
        )

    @Get("/reservations", response_class=HTMLResponse)
    @Shield.need(
        name="chinese_restaurant.reservations_page", action="read", type="template"
    )
    @enqueue_css(Style(href="/app-static/css/app.css"))
    @enqueue_js(Script(src="/app-static/javascript/icons.js", type="module"))
    @enqueue_js(
        Script(src="/app-static/javascript/pages/chinese-restaurant/reservations.js", type="module", defer=True),
        position=Site.HEAD,
    )
    @enqueue_js(
        Script(src="/app-static/javascript/index.js", type="module", defer=True),
        position=Site.BODY_AFTER,
    )
    async def reservations_page(self, request: Request) -> HTMLResponse:
        context = await self._get_common_context(request)
        # Mock reservations
        context.update(
            {
                "reservations": [
                    {
                        "id": 1,
                        "customer": "John Doe",
                        "time": "19:00",
                        "date": "2024-04-22",
                        "table": "T-02",
                        "guests": 4,
                    },
                    {
                        "id": 2,
                        "customer": "Jane Smith",
                        "time": "20:30",
                        "date": "2024-04-22",
                        "table": "T-04",
                        "guests": 2,
                    },
                ]
            }
        )
        return self.templates.TemplateResponse(
            request, name="pages/chinese-restaurant/reservations.html", context=context
        )
