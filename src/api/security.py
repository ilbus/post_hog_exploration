from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from src.config import settings
import secrets

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def validate_api_key(api_key: str = Security(api_key_header)):
    if not api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing API Key")
    if not secrets.compare_digest(api_key, settings.API_SECRET_KEY):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid API Key")
    return api_key
