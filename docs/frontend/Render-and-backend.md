# Rendering and UI-Backend Integration

This document specifies how the application handles template rendering, class-based view registration, and dynamic asset management.

## Template Registration System

The application uses an automated system to discovery and register routes based on Python classes.

### The `Template` Base Class
All UI controllers must inherit from the `Template` class (located in `core/lib/register/template.py`).
- It is agnostic of the rendering engine (Jinja2, Mako, etc.).
- The `template_provider` (e.g., `Jinja2Templates`) is injected into the instance automatically.

### Auto-Router Implementation
Routes are automatically registered in `main.py` using:
- **`auto_router_templates()`**: Scans `src/app/templates` for `Template` subclasses and registers them as routes.
- **`auto_router_partials()`**: Scans `src/app/partials` specifically for HTMX components.

---

## Dynamic Asset Enqueuing

To avoid adding every script and style to the `base.html` manually, the application uses a decorator-based injection system.

### The `_injectable` Pattern
The `base.html` defines several placeholders:
- `{{ _injectable.head.styles }}`
- `{{ _injectable.head.scripts }}`
- `{{ _injectable.body.scripts_after }}`

### Enqueue Decorators
You can "enqueue" specific JS or CSS files directly from the controller method using decorators:

```python
from core.services.ui.enqueue_js import enqueue_js, Site, Script
from core.services.ui.enqueue_css import enqueue_css, CssSite, Style

class MyTemplate(Template):
    @Get("/my-page")
    @enqueue_css(css_tag=str(Style(href="/path/to.css")), position=CssSite.HEAD)
    @enqueue_js(js_tag=str(Script(src="/path/to.js")), position=Site.BODY_AFTER)
    async def my_method(self, request: Request):
        return self.templates.TemplateResponse(...)
```

#### Enqueue Positions
- **Site.HEAD**: Injects into the `<head>` section.
- **Site.BODY_BEFORE**: Injects at the start of the `<body>`.
- **Site.BODY_AFTER**: Injects at the end of the `<body>` (useful for deferring scripts).

---

## Implementation Specifications

### Registering a New Template
1. Create a directory in `src/app/templates/` (e.g., `dashboard/`).
2. Create an HTML file for the view.
3. Create a `template.py` file.
4. Define a class inheriting from `Template`.
5. Annotate methods with `@Get` or `@Post` from `core.lib.decorators`.

### Script and Style Lifecycle
1. The decorator intercepts the request.
2. It appends the requested tags to the `_injectable` global context of the template environment.
3. Once the render is complete, the `_injectable` section is automatically cleared to ensure no leakage between different page requests.
