
from fastapi import FastAPI
import models
from database import engine
from router import auth, todos
from starlette.staticfiles import StaticFiles

app = FastAPI(swagger_ui_parameters={"defaultModelsExpandDepth": -1})

models.Base.metadata.create_all(bind=engine)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(auth.router)
app.include_router(todos.router)
