from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, delete
from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/profiles", tags=["Profiles"])


# 1. 프로필 조회 (GET /profiles/{username})
@router.get("/{username}", response_model=schemas.ProfileResponseWrapper)
async def get_profile(username: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.User).where(models.User.username == username)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # (참고: 로그인 없이 조회하면 팔로우 여부는 false로 나옵니다)
    return {
        "profile": {
            "username": user.username,
            "bio": user.bio,
            "image": user.image,
            "following": False,
        }
    }


# 2. 유저 팔로우 (POST /profiles/{username}/follow)
@router.post("/{username}/follow", response_model=schemas.ProfileResponseWrapper)
async def follow_user(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    result = await db.execute(
        select(models.User).where(models.User.username == username)
    )
    target_user = result.scalars().first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself")

    # 이미 팔로우 중인지 확인
    stmt = select(models.user_follows).where(
        models.user_follows.c.follower_id == current_user.id,
        models.user_follows.c.followed_id == target_user.id,
    )
    existing = await db.execute(stmt)

    if not existing.first():
        await db.execute(
            insert(models.user_follows).values(
                follower_id=current_user.id, followed_id=target_user.id
            )
        )
        await db.commit()

    return {
        "profile": {
            "username": target_user.username,
            "bio": target_user.bio,
            "image": target_user.image,
            "following": True,
        }
    }


# 3. 유저 언팔로우 (DELETE /profiles/{username}/follow)
@router.delete("/{username}/follow", response_model=schemas.ProfileResponseWrapper)
async def unfollow_user(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    result = await db.execute(
        select(models.User).where(models.User.username == username)
    )
    target_user = result.scalars().first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.execute(
        delete(models.user_follows).where(
            models.user_follows.c.follower_id == current_user.id,
            models.user_follows.c.followed_id == target_user.id,
        )
    )
    await db.commit()

    return {
        "profile": {
            "username": target_user.username,
            "bio": target_user.bio,
            "image": target_user.image,
            "following": False,
        }
    }
