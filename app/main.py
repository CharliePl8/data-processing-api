# main.py: Archivo principal de la aplicación FastAPI que configura la API y registra las rutas.
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.csv import router as csv_router
from app.core.config import (
	CORS_ALLOW_CREDENTIALS,
	CORS_HEADERS,
	CORS_MAX_AGE,
	CORS_METHODS,
	CORS_ORIGINS,
)
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware


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

# Middleware de seguridad HTTP
app.add_middleware(SecurityHeadersMiddleware)

# Añadir middleware de rate limiting
app.add_middleware(RateLimitMiddleware)

app.include_router(auth_router)
app.include_router(csv_router)



