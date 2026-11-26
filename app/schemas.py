from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# --- User 관련 스키마 ---
class UserRegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserRegisterWrapper(BaseModel):
    user: UserRegisterRequest

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserLoginWrapper(BaseModel):
    user: UserLoginRequest

class UserResponseData(BaseModel):
    email: EmailStr
    token: str
    username: str
    bio: Optional[str] = None
    image: Optional[str] = None

class UserResponseWrapper(BaseModel):
    user: UserResponseData

# --- Article 관련 스키마 ---
class ArticleAuthor(BaseModel):
    username: str
    bio: Optional[str] = None
    image: Optional[str] = None
    following: bool = False

class ArticleCreateRequest(BaseModel):
    title: str
    description: str
    body: str
    tagList: list[str] = []

class ArticleCreateWrapper(BaseModel):
    article: ArticleCreateRequest

class ArticleResponseData(BaseModel):
    slug: str
    title: str
    description: str
    body: str
    tagList: list[str]
    createdAt: datetime
    updatedAt: datetime
    favorited: bool = False
    favoritesCount: int = 0
    author: ArticleAuthor

class ArticleResponseWrapper(BaseModel):
    article: ArticleResponseData

    class ArticleListResponseWrapper(BaseModel):
        articles: list[ArticleResponseData]
        articlesCount: int

# --- Article 수정용 스키마 ---
class ArticleUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    body: Optional[str] = None

class ArticleUpdateWrapper(BaseModel):
    article: ArticleUpdateRequest

# --- Tag 목록 조회용 스키마 ---
class TagListResponseWrapper(BaseModel):
    tags: list[str]

class ArticleListResponseWrapper(BaseModel):
    articles: list[ArticleResponseData]
    articlesCount: int


    # --- Comment 관련 스키마 ---
class CommentCreateRequest(BaseModel):
    body: str

class CommentCreateWrapper(BaseModel):
    comment: CommentCreateRequest

class CommentResponseData(BaseModel):
    id: int
    body: str
    createdAt: datetime
    updatedAt: datetime
    author: ArticleAuthor

class CommentResponseWrapper(BaseModel):
    comment: CommentResponseData

class CommentListResponseWrapper(BaseModel):
    comments: list[CommentResponseData]

# --- Profile 관련 스키마 ---
class ProfileResponseData(BaseModel):
    username: str
    bio: Optional[str] = None
    image: Optional[str] = None
    following: bool = False

class ProfileResponseWrapper(BaseModel):
    profile: ProfileResponseData