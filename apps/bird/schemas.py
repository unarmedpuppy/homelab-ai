from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class RunBase(BaseModel):
    source: str
    status: str


class RunResponse(RunBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    timestamp: datetime
    post_count: int
    error_message: Optional[str] = None
    created_at: datetime


class RunListResponse(BaseModel):
    runs: list[RunResponse]
    total: int


class PostBase(BaseModel):
    tweet_id: str
    source: str
    author_username: Optional[str] = None
    author_display_name: Optional[str] = None
    content: Optional[str] = None
    url: Optional[str] = None
    media_urls: Optional[str] = None
    tweet_created_at: Optional[datetime] = None


class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    run_id: Optional[str] = None
    fetched_at: datetime


class PostListResponse(BaseModel):
    posts: list[PostResponse]
    total: int
    page: int
    page_size: int
    pages: int


class StatsResponse(BaseModel):
    total_posts: int
    total_runs: int
    latest_run: Optional[RunResponse] = None
    posts_by_source: dict[str, int]
