import os

DEFAULT_ENCODING = "utf-8-sig"
DEFAULT_DELIMITER = ";"
DELIMITER_CANDIDATES = (";", ",", "\t", "|")
NULL_VALUES = ("[NULL]", "NULL")
MAX_FILE_SIZE_BYTES = int(os.getenv("MAX_FILE_SIZE_BYTES", 10 * 1024 * 1024))
DATE_DETECTION_SAMPLE_SIZE = 20
DATE_DETECTION_MIN_PARSE_RATE = 0.8
DEFAULT_OUTPUT_DATE_FORMAT = "%Y-%m-%d"

# Rate limiting (simple in-memory limiter; adecuado para despliegues de un solo proceso)
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", 60))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", 60))

# CORS (Cross-Origin Resource Sharing)
# Orígenes permitidos para acceder a la API
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000",
    ).split(",")
    if origin.strip()
]
# Métodos HTTP permitidos
CORS_METHODS = [method.strip() for method in os.getenv("CORS_METHODS", "GET,POST,OPTIONS").split(",") if method.strip()]
# Cabeceras permitidas en peticiones
CORS_HEADERS = [header.strip() for header in os.getenv("CORS_HEADERS", "*").split(",") if header.strip()]
# Permitir credenciales (cookies, autenticación)
CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "False").lower() in {"1", "true", "yes", "on"}
# Tiempo de caché para respuestas preflight (en segundos)
CORS_MAX_AGE = int(os.getenv("CORS_MAX_AGE", 600))

# Autenticación JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
API_AUTH_USERNAME = os.getenv("API_AUTH_USERNAME", "admin")
API_AUTH_PASSWORD = os.getenv("API_AUTH_PASSWORD", "secret-password")

# Seguridad HTTP adicional
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=()",
}

