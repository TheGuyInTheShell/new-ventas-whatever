def get_wrapper_openapi(is_open: bool = False, prefix: str = "/api/v1"):
    from core.config.settings import settings

    mode = settings.MODE
    if mode != "DEVELOPMENT" and not is_open:
        docs_url = None
        redoc_url = None
        openapi_url = None
    else:
        docs_url = f"/{prefix}/openapi/docs"
        redoc_url = f"/{prefix}/openapi/redoc"
        openapi_url = f"/{prefix}/openapi/openapi.json"
    return docs_url, redoc_url, openapi_url
