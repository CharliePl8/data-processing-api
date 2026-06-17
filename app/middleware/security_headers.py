from typing import Dict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import SECURITY_HEADERS


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware para añadir cabeceras de seguridad HTTP."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response
