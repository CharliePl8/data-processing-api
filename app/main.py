# main.py: Archivo principal de la aplicación FastAPI que configura la API y registra las rutas.
from fastapi import FastAPI

from app.api.routes.csv import router as csv_router

app = FastAPI(title="CSV API", description="API para manejar archivos CSV y convertirlos a JSON", version="1.0.0")

app.include_router(csv_router)



