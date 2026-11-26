import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user
from sqlalchemy import select, func, insert, delete  # 👈 insert, delete 추가

router = APIRouter(prefix="/articles", tags=["Articles"])


# 1. 게시글 작성 (POST /articles)
@router.post(
    "",
    response_model=schemas.ArticleResponseWrapper,
    status_code=status.HTTP_201_CREATED,
)
async def create_article(
    article_in: schemas.ArticleCreateWrapper,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),  # 👈 로그인 필수
):
    data = article_in.article

    # 고유한 slug 생성 (예: my-first-post-a1b2c3d4)
    slug_base = data.title.lower().replace(" ", "-")
    unique_slug = f"{slug_base}-{str(uuid.uuid4())[:8]}"

    # 태그 처리 (없으면 새로 만들고, 있으면 가져옴)
    db_tags = []
    for tag_name in data.tagList:
        result = await db.execute(select(models.Tag).where(models.Tag.name == tag_name))
        tag = result.scalars().first()
        if not tag:
            tag = models.Tag(name=tag_name)
            db.add(tag)
            await db.commit()
            await db.refresh(tag)
        db_tags.append(tag)

    # 게시글 생성
    new_article = models.Article(
        slug=unique_slug,
        title=data.title,
        description=data.description,
        body=data.body,
        author_id=current_user.id,
        tags=db_tags,
    )
    db.add(new_article)
    await db.commit()
    await db.refresh(new_article)

    return {
        "article": {
            "slug": new_article.slug,
            "title": new_article.title,
            "description": new_article.description,
            "body": new_article.body,
            "tagList": [t.name for t in db_tags],
            "createdAt": new_article.created_at,
            "updatedAt": new_article.updated_at,
            "author": {
                "username": current_user.username,
                "bio": current_user.bio,
                "image": current_user.image,
                "following": False,
            },
        }
    }


# 2. 게시글 단일 조회 (GET /articles/{slug})
@router.get("/{slug}", response_model=schemas.ArticleResponseWrapper)
async def get_article(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Article).where(models.Article.slug == slug))
    article = result.scalars().first()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # 작성자 정보 및 태그 정보 로드 (Async SQLAlchemy 이슈 방지)
    await db.refresh(article, ["author", "tags"])

    return {
        "article": {
            "slug": article.slug,
            "title": article.title,
            "description": article.description,
            "body": article.body,
            "tagList": [t.name for t in article.tags],
            "createdAt": article.created_at,
            "updatedAt": article.updated_at,
            "author": {
                "username": article.author.username,
                "bio": article.author.bio,
                "image": article.author.image,
                "following": False,
            },
        }
    }

    # 3. 게시글 전체 목록 조회 (GET /articles)


@router.get("", response_model=schemas.ArticleListResponseWrapper)
async def list_articles(
    tag: str | None = None,
    author: str | None = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    # 기본 쿼리 생성
    stmt = select(models.Article).join(models.User)

    if tag:
        stmt = stmt.join(models.Article.tags).where(models.Tag.name == tag)
    if author:
        stmt = stmt.where(models.User.username == author)

    stmt = stmt.order_by(models.Article.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(stmt)
    articles = result.scalars().all()

    # 전체 개수 조회 (페이지네이션용)
    count_stmt = select(func.count()).select_from(models.Article)
    if tag:
        count_stmt = count_stmt.join(models.Article.tags).where(models.Tag.name == tag)
    if author:
        count_stmt = count_stmt.join(models.User).where(models.User.username == author)
    count_result = await db.execute(count_stmt)
    total_count = count_result.scalar()

    # 응답 형식에 맞게 변환
    articles_data = []
    for article in articles:
        await db.refresh(article, ["author", "tags"])
        articles_data.append(
            {
                "slug": article.slug,
                "title": article.title,
                "description": article.description,
                "body": article.body,
                "tagList": [t.name for t in article.tags],
                "createdAt": article.created_at,
                "updatedAt": article.updated_at,
                "favorited": False,
                "favoritesCount": 0,
                "author": {
                    "username": article.author.username,
                    "bio": article.author.bio,
                    "image": article.author.image,
                    "following": False,
                },
            }
        )

    return {"articles": articles_data, "articlesCount": total_count}


# 4. 게시글 수정 (PUT /articles/{slug})
@router.put("/{slug}", response_model=schemas.ArticleResponseWrapper)
async def update_article(
    slug: str,
    article_in: schemas.ArticleUpdateWrapper,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    result = await db.execute(select(models.Article).where(models.Article.slug == slug))
    article = result.scalars().first()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # 작성자 본인인지 확인
    if article.author_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this article"
        )

    # 수정할 데이터만 업데이트
    data = article_in.article
    if data.title is not None:
        article.title = data.title
    if data.description is not None:
        article.description = data.description
    if data.body is not None:
        article.body = data.body

    await db.commit()
    await db.refresh(article, ["author", "tags"])

    return {
        "article": {
            "slug": article.slug,
            "title": article.title,
            "description": article.description,
            "body": article.body,
            "tagList": [t.name for t in article.tags],
            "createdAt": article.created_at,
            "updatedAt": article.updated_at,
            "author": {
                "username": current_user.username,
                "bio": current_user.bio,
                "image": current_user.image,
                "following": False,
            },
        }
    }


# 5. 게시글 삭제 (DELETE /articles/{slug})
@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    result = await db.execute(select(models.Article).where(models.Article.slug == slug))
    article = result.scalars().first()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    if article.author_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this article"
        )

    await db.delete(article)
    await db.commit()
    return None


# 6. 게시글 좋아요 (POST /articles/{slug}/favorite)
@router.post("/{slug}/favorite", response_model=schemas.ArticleResponseWrapper)
async def favorite_article(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    result = await db.execute(select(models.Article).where(models.Article.slug == slug))
    article = result.scalars().first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # 이미 좋아요를 눌렀는지 확인 후 추가
    stmt = select(models.article_favorites).where(
        models.article_favorites.c.user_id == current_user.id,
        models.article_favorites.c.article_id == article.id,
    )
    existing = await db.execute(stmt)
    if not existing.first():
        await db.execute(
            insert(models.article_favorites).values(
                user_id=current_user.id, article_id=article.id
            )
        )
        await db.commit()

    return await get_article(slug, db)


# 7. 게시글 좋아요 취소 (DELETE /articles/{slug}/favorite)
@router.delete("/{slug}/favorite", response_model=schemas.ArticleResponseWrapper)
async def unfavorite_article(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    result = await db.execute(select(models.Article).where(models.Article.slug == slug))
    article = result.scalars().first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    await db.execute(
        delete(models.article_favorites).where(
            models.article_favorites.c.user_id == current_user.id,
            models.article_favorites.c.article_id == article.id,
        )
    )
    await db.commit()

    return await get_article(slug, db)


# 8. 피드 조회 (팔로우한 유저의 글만 보기) (GET /articles/feed)
@router.get("/feed", response_model=schemas.ArticleListResponseWrapper)
async def get_feed(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # 내가 팔로우한 유저들의 ID 목록 가져오기
    follow_stmt = select(models.user_follows.c.followed_id).where(
        models.user_follows.c.follower_id == current_user.id
    )
    follow_result = await db.execute(follow_stmt)
    followed_ids = follow_result.scalars().all()

    if not followed_ids:
        return {"articles": [], "articlesCount": 0}

    # 팔로우한 유저들의 글만 최신순으로 가져오기
    stmt = (
        select(models.Article)
        .where(models.Article.author_id.in_(followed_ids))
        .order_by(models.Article.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    articles = result.scalars().all()

    articles_data = []
    for article in articles:
        await db.refresh(article, ["author", "tags"])
        articles_data.append(
            {
                "slug": article.slug,
                "title": article.title,
                "description": article.description,
                "body": article.body,
                "tagList": [t.name for t in article.tags],
                "createdAt": article.created_at,
                "updatedAt": article.updated_at,
                "favorited": False,
                "favoritesCount": 0,
                "author": {
                    "username": article.author.username,
                    "bio": article.author.bio,
                    "image": article.author.image,
                    "following": True,  # 피드니까 무조건 팔로우 상태
                },
            }
        )
    return {"articles": articles_data, "articlesCount": len(articles_data)}
