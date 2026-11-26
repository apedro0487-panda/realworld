from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models, schemas
from app.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/users", tags=["Authentication"])

# 1. 회원가입 (POST /users)
@router.post("", response_model=schemas.UserResponseWrapper, status_code=status.HTTP_201_CREATED)
async def register(user_in: schemas.UserRegisterWrapper, db: AsyncSession = Depends(get_db)):
    data = user_in.user
    
    # 이메일 또는 유저네임 중복 검사
    existing = await db.execute(select(models.User).where(
        (models.User.email == data.email) | (models.User.username == data.username)
    ))
    if existing.scalars().first():
        raise HTTPException(status_code=422, detail="Email or username already exists")

    # 유저 생성 및 저장
    new_user = models.User(
        email=data.email,
        username=data.username,
        hashed_password=get_password_hash(data.password)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # 토큰 발급 (이메일을 subject로 사용)
    token = create_access_token({"sub": new_user.email})

    return {
        "user": {
            "email": new_user.email,
            "token": token,
            "username": new_user.username,
            "bio": new_user.bio,
            "image": new_user.image
        }
    }

# 2. 로그인 (POST /users/login)
@router.post("/login", response_model=schemas.UserResponseWrapper)
async def login(user_in: schemas.UserLoginWrapper, db: AsyncSession = Depends(get_db)):
    data = user_in.user
    
    result = await db.execute(select(models.User).where(models.User.email == data.email))
    user = result.scalars().first()
    
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=422, detail="Incorrect email or password")
        
    token = create_access_token({"sub": user.email})

    return {
        "user": {
            "email": user.email,
            "token": token,
            "username": user.username,
            "bio": user.bio,
            "image": user.image
        }
    }