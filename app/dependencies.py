from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.database import get_db
from app.core.security import decode_access_token
from app import models

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

async def get_current_user(
    authorization: Optional[str] = Depends(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> models.User:
    if not authorization or not authorization.startswith("Token "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await db.execute(select(models.User).where(models.User.email == payload["sub"]))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user