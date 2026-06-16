import time
from typing import Dict, List

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS



class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware sencillo de limitación de tasa en memoria.

    - Cuenta peticiones por dirección IP en una ventana temporal deslizante.
    - Implementa un algoritmo simple de sliding window.
    - Añade cabeceras `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` y `Retry-After`.
    - Nota: está limitada a un único proceso. Para múltiples procesos/instancias, considera Redis.
    """

    def __init__(self, app):
        super().__init__(app)
        # Mapeo de cliente(IP) -> lista de timestamps de peticiones
        self.hits: Dict[str, List[float]] = {}

    async def dispatch(self, request: Request, call_next) -> Response:
        # Determinar identificador del cliente (IP)
        client = "unknown"
        if request.client and request.client.host:
            client = request.client.host

        now = time.time()
        window = RATE_LIMIT_WINDOW_SECONDS
        limit = RATE_LIMIT_REQUESTS

        # Obtener lista de timestamps para este cliente
        timestamps = self.hits.get(client, [])
        cutoff = now - window
        # Mantener solo los timestamps dentro de la ventana
        timestamps = [t for t in timestamps if t > cutoff]

        # Verificar si se excedió el límite
        if len(timestamps) >= limit:
            # Calcular tiempo hasta que se libere el siguiente slot
            retry_after = int(window - (now - timestamps[0])) if timestamps else window
            return JSONResponse(
                status_code=429,
                content={"detail": "Demasiadas peticiones. Intenta más tarde."},
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(retry_after),
                },
            )

        # Registrar la petición actual
        timestamps.append(now)
        self.hits[client] = timestamps

        # Procesar la petición
        response = await call_next(request)

        # Añadir cabeceras de rate limit a la respuesta
        remaining = max(0, limit - len(timestamps))
        reset = int(window - (now - timestamps[0])) if timestamps else window
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset)

        return response
