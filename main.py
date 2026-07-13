import os

import uvicorn
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles

from src.api import doc, user_manager_api
from src.config import config

settings = config.Settings()

project_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__))))
static_dir = os.path.join(project_dir, "resources/static")


app = FastAPI(docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(doc.router)
app.include_router(user_manager_api.router)


def modify_route_names_as_operation_ids(app: FastAPI) -> None:
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name  # in this case, 'read_items'


modify_route_names_as_operation_ids(app)

if __name__ == "__main__":
    uvicorn.run(app="main:app", host=settings.host, port=settings.port, reload=True)
