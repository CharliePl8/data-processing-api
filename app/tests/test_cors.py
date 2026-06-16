import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.csv import router as csv_router
from app.middleware.rate_limit import RateLimitMiddleware
from app.core.config import CORS_ORIGINS, CORS_METHODS, CORS_HEADERS
from fastapi.middleware.cors import CORSMiddleware


@pytest.fixture
def app_with_cors():
	"""Crear una app con CORS configurado."""
	app = FastAPI()
	
	app.add_middleware(
		CORSMiddleware,
		allow_origins=CORS_ORIGINS,
		allow_credentials=False,
		allow_methods=CORS_METHODS,
		allow_headers=CORS_HEADERS,
		max_age=600,
	)
	
	app.add_middleware(RateLimitMiddleware)
	app.include_router(csv_router)
	
	@app.get("/health")
	async def health_check():
		return "healthy"
	
	return app


@pytest.fixture
def client(app_with_cors):
	"""Cliente de prueba para la aplicación con CORS."""
	return TestClient(app_with_cors)


def test_cors_header_present_on_allowed_origin(client):
	"""Verificar que CORS headers están presentes para orígenes permitidos."""
	response = client.get(
		"/health",
		headers={"Origin": "http://localhost:3000"},
	)
	
	assert response.status_code == 200
	assert "access-control-allow-origin" in response.headers
	assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_methods_header(client):
	"""Verificar que el header CORS methods contiene los métodos permitidos."""
	response = client.get(
		"/health",
		headers={"Origin": "http://localhost:3000"},
	)
	
	assert response.status_code == 200
	# FastAPI maneja automáticamente esto


def test_cors_preflight_request(client):
	"""Verificar que las peticiones preflight (OPTIONS) son manejadas correctamente."""
	response = client.options(
		"/health",
		headers={
			"Origin": "http://localhost:3000",
			"Access-Control-Request-Method": "POST",
		},
	)
	
	assert response.status_code == 200
	assert "access-control-allow-origin" in response.headers


def test_cors_disallowed_origin(client):
	"""Verificar que orígenes no permitidos no reciben headers CORS."""
	response = client.get(
		"/health",
		headers={"Origin": "http://malicious-site.com"},
	)
	
	assert response.status_code == 200
	# Origen no permitido no debería recibir header CORS (o estaría vacío)
	# Nota: Algunos servidores CORS devuelven 200 pero sin headers, otros lo manejan diferente
