"""
Bird Database Module

SQLAlchemy models and database utilities for the Bird bookmark processor
and Bird Viewer UI. Uses SQLite for persistent storage.
"""

import os
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

# Database configuration
DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/bird.db")

Base = declarative_base()


def generate_id() -> str:
    """Generate a short unique ID."""
    return uuid.uuid4().hex[:12]


class RunStatus(str, Enum):
    """Status of a processing run."""
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


class RunSource(str, Enum):
    """Source of tweets for a run."""
    BOOKMARKS = "bookmarks"
    LIKES = "likes"
    MANUAL = "manual"
    MIXED = "mixed"


class ApprovalStatus(str, Enum):
    """Approval status for a post."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Run(Base):
    """A processing run that fetched tweets."""
    __tablename__ = "runs"

    id = Column(String(12), primary_key=True, default=generate_id)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    source = Column(String(20), nullable=False)  # RunSource value
    status = Column(String(20), nullable=False, default=RunStatus.RUNNING.value)
    post_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    posts = relationship("Post", back_populates="run", lazy="dynamic")

    def __repr__(self):
        return f"<Run {self.id} {self.source} {self.status}>"


class Post(Base):
    """A fetched tweet/post."""
    __tablename__ = "posts"

    id = Column(String(12), primary_key=True, default=generate_id)
    run_id = Column(String(12), ForeignKey("runs.id"), nullable=True)
    tweet_id = Column(String(30), unique=True, nullable=False)
    author_username = Column(String(100), nullable=True)
    author_display_name = Column(String(200), nullable=True)
    content = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    media_urls = Column(Text, nullable=True)  # JSON array
    tweet_created_at = Column(DateTime, nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    run = relationship("Run", back_populates="posts")
    categorizations = relationship(
        "Categorization", back_populates="post", lazy="dynamic",
        order_by="desc(Categorization.created_at)"
    )
    approval = relationship("Approval", back_populates="post", uselist=False)

    @property
    def latest_categorization(self) -> Optional["Categorization"]:
        """Get the most recent categorization."""
        return self.categorizations.first()

    def __repr__(self):
        return f"<Post {self.id} @{self.author_username}>"


class Categorization(Base):
    """AI categorization of a post. Multiple per post for history."""
    __tablename__ = "categorizations"

    id = Column(String(12), primary_key=True, default=generate_id)
    post_id = Column(String(12), ForeignKey("posts.id"), nullable=False)
    category = Column(String(50), nullable=True)  # technologies, concepts, resources, projects, other
    tags = Column(Text, nullable=True)  # JSON array
    confidence = Column(Float, nullable=True)
    reasoning = Column(Text, nullable=True)
    model_used = Column(String(100), nullable=True)
    is_override = Column(Boolean, default=False)  # True if manually overridden
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    post = relationship("Post", back_populates="categorizations")

    def __repr__(self):
        return f"<Categorization {self.id} {self.category}>"


class Approval(Base):
    """Approval workflow for a post."""
    __tablename__ = "approvals"

    id = Column(String(12), primary_key=True, default=generate_id)
    post_id = Column(String(12), ForeignKey("posts.id"), unique=True, nullable=False)
    status = Column(String(20), nullable=False, default=ApprovalStatus.PENDING.value)
    learning_list_entry = Column(Text, nullable=True)  # Generated markdown
    edited_entry = Column(Text, nullable=True)  # User-edited version
    written_at = Column(DateTime, nullable=True)  # When written to learning-list.md
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    post = relationship("Post", back_populates="approval")

    @property
    def final_entry(self) -> Optional[str]:
        """Get the entry to write (edited if available, otherwise generated)."""
        return self.edited_entry or self.learning_list_entry

    def __repr__(self):
        return f"<Approval {self.id} {self.status}>"


# Create indexes for common queries
Index("idx_posts_run", Post.run_id)
Index("idx_posts_tweet", Post.tweet_id)
Index("idx_categorizations_post", Categorization.post_id)
Index("idx_approvals_status", Approval.status)
Index("idx_runs_timestamp", Run.timestamp.desc())


# Database session management
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        # Ensure data directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False}  # SQLite specific
        )
    return _engine


def get_session_factory():
    """Get or create the session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def init_db():
    """Initialize the database, creating tables if needed."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get a database session. Use as context manager or generator for FastAPI."""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DatabaseSession:
    """Context manager for database sessions."""
    
    def __init__(self):
        self.db = None
    
    def __enter__(self):
        SessionLocal = get_session_factory()
        self.db = SessionLocal()
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            self.db.close()


# Convenience functions for common operations

def get_or_create_post(db, tweet_id: str, **kwargs) -> tuple[Post, bool]:
    """Get existing post by tweet_id or create new one. Returns (post, created)."""
    post = db.query(Post).filter(Post.tweet_id == tweet_id).first()
    if post:
        return post, False
    
    post = Post(tweet_id=tweet_id, **kwargs)
    db.add(post)
    return post, True


def get_pending_approvals(db, limit: int = 100) -> list[Post]:
    """Get posts pending approval."""
    return (
        db.query(Post)
        .join(Approval)
        .filter(Approval.status == ApprovalStatus.PENDING.value)
        .order_by(Post.fetched_at.desc())
        .limit(limit)
        .all()
    )


def get_run_with_posts(db, run_id: str) -> Optional[Run]:
    """Get a run with its posts."""
    return db.query(Run).filter(Run.id == run_id).first()


def create_run(db, source: str) -> Run:
    """Create a new processing run."""
    run = Run(source=source, status=RunStatus.RUNNING.value)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def complete_run(db, run: Run, success: bool = True, error: str = None, post_count: int = 0):
    """Mark a run as complete."""
    run.status = RunStatus.SUCCESS.value if success else RunStatus.ERROR.value
    run.error_message = error
    run.post_count = post_count
    db.commit()


if __name__ == "__main__":
    # Initialize database when run directly
    print(f"Initializing database at {DATABASE_URL}")
    init_db()
    print("Database initialized successfully!")
