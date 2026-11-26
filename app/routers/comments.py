from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(tags=["Comments"])


# 1. 댓글 작성 (POST /articles/{slug}/comments)
@router.post(
    "/articles/{slug}/comments",
    response_model=schemas.CommentResponseWrapper,
    status_code=status.HTTP_201_CREATED,
)
async def add_comment(
    slug: str,
    comment_in: schemas.CommentCreateWrapper,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    result = await db.execute(select(models.Article).where(models.Article.slug == slug))
    article = result.scalars().first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    new_comment = models.Comment(
        body=comment_in.comment.body, article_id=article.id, author_id=current_user.id
    )
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)

    return {
        "comment": {
            "id": new_comment.id,
            "body": new_comment.body,
            "createdAt": new_comment.created_at,
            "updatedAt": new_comment.updated_at,
            "author": {
                "username": current_user.username,
                "bio": current_user.bio,
                "image": current_user.image,
                "following": False,
            },
        }
    }


# 2. 댓글 목록 조회 (GET /articles/{slug}/comments)
@router.get(
    "/articles/{slug}/comments", response_model=schemas.CommentListResponseWrapper
)
async def get_comments(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Article).where(models.Article.slug == slug))
    article = result.scalars().first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    stmt = (
        select(models.Comment)
        .where(models.Comment.article_id == article.id)
        .order_by(models.Comment.created_at.desc())
    )
    comments_result = await db.execute(stmt)
    comments = comments_result.scalars().all()

    comments_data = []
    for c in comments:
        await db.refresh(c, ["author"])
        comments_data.append(
            {
                "id": c.id,
                "body": c.body,
                "createdAt": c.created_at,
                "updatedAt": c.updated_at,
                "author": {
                    "username": c.author.username,
                    "bio": c.author.bio,
                    "image": c.author.image,
                    "following": False,
                },
            }
        )
    return {"comments": comments_data}


# 3. 댓글 삭제 (DELETE /articles/{slug}/comments/{id})
@router.delete("/articles/{slug}/comments/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    slug: str,
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    result = await db.execute(select(models.Comment).where(models.Comment.id == id))
    comment = result.scalars().first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.author_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this comment"
        )

    await db.delete(comment)
    await db.commit()
    return None
