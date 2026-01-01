#!/usr/bin/env python3
from contextlib import asynccontextmanager
from math import ceil
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import Post, Run, get_db, init_db
from schemas import (
    PostListResponse,
    PostResponse,
    RunListResponse,
    RunResponse,
    StatsResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Bird Viewer API",
    description="API for viewing stored Twitter/X bookmarks",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db_session():
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "bird-viewer-api"}


@app.get("/runs", response_model=RunListResponse)
async def list_runs(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db_session),
):
    total = db.query(func.count(Run.id)).scalar()
    runs = (
        db.query(Run)
        .order_by(Run.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return RunListResponse(runs=runs, total=total)


@app.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(run_id: str, db: Session = Depends(get_db_session)):
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@app.get("/posts", response_model=PostListResponse)
async def list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    run_id: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db_session),
):
    query = db.query(Post)
    
    if run_id:
        query = query.filter(Post.run_id == run_id)
    
    if author:
        query = query.filter(Post.author_username.ilike(f"%{author}%"))
    
    if search:
        query = query.filter(Post.content.ilike(f"%{search}%"))
    
    total = query.count()
    pages = ceil(total / page_size) if total > 0 else 1
    
    posts = (
        query
        .order_by(Post.fetched_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    
    return PostListResponse(
        posts=posts,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@app.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(post_id: str, db: Session = Depends(get_db_session)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@app.get("/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db_session)):
    total_posts = db.query(func.count(Post.id)).scalar()
    total_runs = db.query(func.count(Run.id)).scalar()
    
    latest_run = db.query(Run).order_by(Run.timestamp.desc()).first()
    
    posts_by_source = {}
    source_counts = (
        db.query(Run.source, func.count(Post.id))
        .join(Post, Run.id == Post.run_id)
        .group_by(Run.source)
        .all()
    )
    for source, count in source_counts:
        posts_by_source[source] = count
    
    return StatsResponse(
        total_posts=total_posts,
        total_runs=total_runs,
        latest_run=latest_run,
        posts_by_source=posts_by_source,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
