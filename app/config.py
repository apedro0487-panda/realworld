from fastapi import FastAPI
from app.database import engine, Base
from app.routers import auth  # 👈 auth만 import 합니다
from app.routers import auth, articles  # 👈 articles
from app.routers import auth, articles, tags  # 👈 tags 추가 추가.
from app.routers import auth, articles, tags, comments, profiles  # 👈 추가
from fastapi.middleware.cors import CORSMiddleware
from config import settings

app = FastAPI(title="RealWorld API")

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(auth.router) # 👈 auth만 등록합니다.
app.include_router(articles.router)  # 👈 articles 라우터 등록
app.include_router(tags.router)  # 👈 tags 등록
app.include_router(comments.router)  # 👈 추가
app.include_router(profiles.router)  # 👈 추가

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)