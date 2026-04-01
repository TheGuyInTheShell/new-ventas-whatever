from fastapi.templating import Jinja2Templates
from fastapi import FastAPI

templates = Jinja2Templates(directory="admin/src")


app = FastAPI(
    title="FastAPI Template",
)