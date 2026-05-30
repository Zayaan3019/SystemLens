from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status

from systemlens.config import load_config


@dataclass
class AuthContext:
    role: str


def _get_token(request: Request) -> str | None:
    header = request.headers.get("authorization") or request.headers.get("Authorization")
    if header and header.lower().startswith("bearer "):
        return header.split(" ", 1)[1].strip()
    token = request.headers.get("X-Auth-Token")
    if token:
        return token.strip()
    query = request.query_params.get("token")
    if query:
        return query.strip()
    return None


def _resolve_role(token: str | None, config) -> str | None:
    if not token:
        return None
    if config.admin_token and token == config.admin_token:
        return "admin"
    if config.viewer_token and token == config.viewer_token:
        return "viewer"
    return None


def require_role(required: str):
    config = load_config()

    async def _dependency(request: Request) -> AuthContext:
        if not config.auth_enabled:
            return AuthContext(role="admin")
        token = _get_token(request)
        role = _resolve_role(token, config)
        if role is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
        if required == "admin" and role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return AuthContext(role=role)

    return Depends(_dependency)
