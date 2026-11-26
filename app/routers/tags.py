from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/tags", tags=["Tags"])

@router.get("", response_model=schemas.TagListResponseWrapper)
async def get_tags(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Tag.name))
    tags = result.scalars().all()
    return {"tags": tags}