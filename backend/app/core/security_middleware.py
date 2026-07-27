"""
Security middleware for production:
- Request size limiting
- Security headers
- Brute force protection on login
- Suspicious request detection
"""
import time
import logging
from collections import defaultdict
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings

logger = logging.getLogger("texlify.security")

# ── In-memory stores ──────────────────────────────────────────────────────────
_login_attempts: dict = defaultdict(list)   # ip -> [timestamps]
_blocked_ips:    dict = {}                  # ip -> unblock_time


class SecurityMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request,
                       call_next: Callable) -> Response:

        client_ip = self._get_client_ip(request)

        # 1. Block banned IPs
        if client_ip in _blocked_ips:
            if time.time() < _blocked_ips[client_ip]:
                logger.warning(f"Blocked IP attempted access: {client_ip}")
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many failed attempts. Try again later."}
                )
            else:
                del _blocked_ips[client_ip]

        # 2. Request size limiting
        content_length = request.headers.get("content-length")
        if content_length:
            size_mb = int(content_length) / (1024 * 1024)
            if size_mb > settings.MAX_REQUEST_SIZE_MB:
                logger.warning(
                    f"Request too large from {client_ip}: {size_mb:.1f}MB")
                return JSONResponse(
                    status_code=413,
                    content={"detail": f"Request too large. Max {settings.MAX_REQUEST_SIZE_MB}MB."}
                )

        # 3. Brute force protection on login
        if (request.url.path.endswith("/auth/login")
                and request.method == "POST"):
            if not self._check_login_rate_limit(client_ip):
                logger.warning(f"Brute force detected from {client_ip}")
                # Block IP for 15 minutes
                _blocked_ips[client_ip] = time.time() + 900
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": (
                            "Too many login attempts. "
                            "Account locked for 15 minutes."
                        )
                    }
                )

        # 4. Process request
        response = await call_next(request)

        # 5. Add security headers
        response.headers["X-Content-Type-Options"]    = "nosniff"
        response.headers["X-Frame-Options"]           = "DENY"
        response.headers["X-XSS-Protection"]          = "1; mode=block"
        response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"]        = (
            "geolocation=(), microphone=(), camera=()"
        )
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # 6. Track failed logins
        if (request.url.path.endswith("/auth/login")
                and response.status_code == 401):
            self._record_failed_login(client_ip)

        return response

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def _check_login_rate_limit(self, ip: str) -> bool:
        now      = time.time()
        window   = settings.RATE_LIMIT_LOGIN_WINDOW_SEC
        max_att  = settings.RATE_LIMIT_LOGIN_ATTEMPTS
        attempts = [t for t in _login_attempts[ip] if now - t < window]
        _login_attempts[ip] = attempts
        return len(attempts) < max_att

    def _record_failed_login(self, ip: str):
        _login_attempts[ip].append(time.time())
        logger.warning(
            f"Failed login from {ip} "
            f"(attempt {len(_login_attempts[ip])})"
        )