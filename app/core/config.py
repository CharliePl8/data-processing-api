DEFAULT_ENCODING = "utf-8-sig"
DEFAULT_DELIMITER = ";"
DELIMITER_CANDIDATES = (";", ",", "\t", "|")
NULL_VALUES = ("[NULL]", "NULL")
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
DATE_DETECTION_SAMPLE_SIZE = 20
DATE_DETECTION_MIN_PARSE_RATE = 0.8
DEFAULT_OUTPUT_DATE_FORMAT = "%Y-%m-%d"

# Rate limiting (simple in-memory limiter; adecuado para despliegues de un solo proceso)
RATE_LIMIT_REQUESTS = 60  # número de peticiones permitidas
RATE_LIMIT_WINDOW_SECONDS = 60  # ventana en segundos

# CORS (Cross-Origin Resource Sharing)
# Orígenes permitidos para acceder a la API
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]
# Métodos HTTP permitidos
CORS_METHODS = ["GET", "POST", "OPTIONS"]
# Cabeceras permitidas en peticiones
CORS_HEADERS = ["*"]
# Permitir credenciales (cookies, autenticación)
CORS_ALLOW_CREDENTIALS = False
# Tiempo de caché para respuestas preflight (en segundos)
CORS_MAX_AGE = 600

# Autenticación JWT
JWT_SECRET_KEY = "c4f88d92d8bd4f7d87b4ca02c556a22f"  # Cambia esto en producción
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
API_AUTH_USERNAME = "admin"
API_AUTH_PASSWORD = "secret-password"

# Seguridad HTTP adicional
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=()",
}

