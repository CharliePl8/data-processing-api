# main.py: Archivo principal de la aplicación FastAPI que configura la API y registra las rutas.
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.csv import router as csv_router
from app.middleware.rate_limit import RateLimitMiddleware
from app.core.config import (
	CORS_ORIGINS,
	CORS_METHODS,
	CORS_HEADERS,
	CORS_ALLOW_CREDENTIALS,
	CORS_MAX_AGE,
)


app = FastAPI(title="CSV API", description="API para manejar archivos CSV y convertirlos a JSON", version="1.0.0")

# Middleware de CORS (debe estar antes de otros middlewares)
app.add_middleware(
	CORSMiddleware,
	allow_origins=CORS_ORIGINS,
	allow_credentials=CORS_ALLOW_CREDENTIALS,
	allow_methods=CORS_METHODS,
	allow_headers=CORS_HEADERS,
	max_age=CORS_MAX_AGE,
)

# Añadir middleware de rate limiting
app.add_middleware(RateLimitMiddleware)

app.include_router(csv_router)



