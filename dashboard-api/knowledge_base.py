# Knowledge Base API Module
"""
FastAPI endpoints for the personal knowledge base system.
Provides CRUD operations, search, and categorization management.
"""

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import json
import yaml
import shutil
from pathlib import Path

router = APIRouter(prefix="/kb", tags=["knowledge-base"])

# =============================================================================
# Data Models
# =============================================================================

class KnowledgeItem(BaseModel):
    """Represents a knowledge base item."""
    id: str
    title: str
    content: str
    category: str
    tags: List[str]
    created_at: str
    updated_at: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    author: Optional[str] = None
    
class KnowledgeFile(BaseModel):
    """File information for knowledge base."""
    path: str
    name: str
    size: int
    modified: str
    category: str
    
class SearchResults(BaseModel):
    """Search results with relevance scores."""
    results: List[Dict[str, Any]]
    total: int
    query: str
    
class CategoryStats(BaseModel):
    """Statistics for a category."""
    name: str
    count: int
    total_size: int
    last_updated: Optional[str] = None
    
# =============================================================================
# Helper Functions
# =============================================================================

def get_kb_path() -> Path:
    """Get the knowledge base directory path."""
    return Path(os.path.expanduser("~/.obsidian/knowledge-base"))

def get_config_path() -> Path:
    """Get the configuration file path."""
    return Path("/Users/aijenquist/workspace/personal-kb/config.yaml")

def load_config() -> Dict[str, Any]:
    """Load configuration file."""
    config_path = get_config_path()
    if not config_path.exists():
        raise HTTPException(status_code=500, detail="Configuration file not found")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def get_category_path(category: str) -> Path:
    """Get the path for a specific category."""
    kb_path = get_kb_path()
    return kb_path / category

def list_files_in_category(category: str) -> List[KnowledgeFile]:
    """List all files in a category."""
    category_path = get_category_path(category)
    if not category_path.exists():
        return []
    
    files = []
    for file_path in category_path.iterdir():
        if file_path.is_file() and file_path.suffix == '.md':
            stat = file_path.stat()
            files.append(KnowledgeFile(
                path=str(file_path),
                name=file_path.name,
                size=stat.st_size,
                modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                category=category
            ))
    
    return sorted(files, key=lambda x: x.modified, reverse=True)

def read_file_content(file_path: Path) -> str:
    """Read content from a file."""
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def parse_frontmatter(content: str) -> Dict[str, Any]:
    """Parse YAML frontmatter from Markdown content."""
    if not content.startswith('---'):
        return {}
    
    try:
        end_marker = content.find('---', 3)
        if end_marker == -1:
            return {}
        
        frontmatter_yaml = content[3:end_marker].strip()
        return yaml.safe_load(frontmatter_yaml) or {}
    except:
        return {}

# =============================================================================
# API Endpoints
# =============================================================================

@router.get("/")
async def get_kb_info():
    """Get knowledge base information."""
    kb_path = get_kb_path()
    
    if not kb_path.exists():
        return {
            "exists": False,
            "path": str(kb_path),
            "message": "Knowledge base not initialized"
        }
    
    # Get categories
    categories = []
    for item in kb_path.iterdir():
        if item.is_dir():
            categories.append({
                "name": item.name,
                "path": str(item),
                "exists": True
            })
    
    return {
        "exists": True,
        "path": str(kb_path),
        "categories": sorted(categories, key=lambda x: x["name"]),
        "config": load_config()
    }

@router.get("/categories")
async def list_categories():
    """List all categories in the knowledge base."""
    kb_path = get_kb_path()
    
    if not kb_path.exists():
        return {"categories": []}
    
    categories = []
    for item in kb_path.iterdir():
        if item.is_dir():
            categories.append(item.name)
    
    return {"categories": sorted(categories)}

@router.get("/categories/{category}/files")
async def list_category_files(category: str):
    """List all files in a specific category."""
    files = list_files_in_category(category)
    return {"files": files, "category": category}

@router.get("/categories/{category}/stats")
async def get_category_stats(category: str):
    """Get statistics for a category."""
    category_path = get_category_path(category)
    
    if not category_path.exists():
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")
    
    count = 0
    total_size = 0
    last_updated = None
    
    for file_path in category_path.iterdir():
        if file_path.is_file() and file_path.suffix == '.md':
            count += 1
            total_size += file_path.stat().st_size
            stat = file_path.stat()
            if last_updated is None or stat.st_mtime > last_updated:
                last_updated = datetime.fromtimestamp(stat.st_mtime).isoformat()
    
    return CategoryStats(
        name=category,
        count=count,
        total_size=total_size,
        last_updated=last_updated
    )

@router.get("/files/{file_path:path}")
async def get_file_content(file_path: str):
    """Get content of a specific file."""
    full_path = Path(file_path)
    
    if not full_path.is_absolute():
        # Try relative to kb path
        full_path = get_kb_path() / file_path
    
    if not full_path.exists():
        # Try other common paths
        alternative_paths = [
            Path("/Users/aijenquist/workspace/personal-kb") / file_path,
            Path.home() / file_path
        ]
        for alt_path in alternative_paths:
            if alt_path.exists():
                full_path = alt_path
                break
        else:
            raise HTTPException(status_code=404, detail="File not found")
    
    content = read_file_content(full_path)
    frontmatter = parse_frontmatter(content)
    
    return {
        "path": str(full_path),
        "content": content,
        "frontmatter": frontmatter,
        "size": full_path.stat().st_size
    }

@router.post("/add")
async def add_content(item: KnowledgeItem):
    """Add new content to the knowledge base."""
    kb_path = get_kb_path()
    category_path = get_category_path(item.category)
    
    # Create category if it doesn't exist
    category_path.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_title = item.title.replace("/", "-").replace("\\", "-")[:50]
    filename = f"{timestamp}-{safe_title}.md"
    file_path = category_path / filename
    
    # Build Markdown content
    frontmatter = f"""---
id: {item.id}
source: {item.source or "manual"}
author: {item.author or "user"}
categories: {json.dumps(item.category)}
tags: {json.dumps(item.tags)}
created_at: {item.created_at}
---
"""
    
    markdown_content = frontmatter + "\n" + item.content
    
    # Write file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    return {
        "success": True,
        "path": str(file_path),
        "category": item.category,
        "filename": filename
    }

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), category: str = "Other"):
    """Upload a file to the knowledge base."""
    kb_path = get_kb_path()
    category_path = get_category_path(category)
    
    # Create category if it doesn't exist
    category_path.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file_path = category_path / file.filename
    with open(file_path, 'wb') as f:
        f.write(await file.read())
    
    return {
        "success": True,
        "path": str(file_path),
        "category": category,
        "filename": file.filename,
        "size": len(await file.read())
    }

@router.delete("/files/{file_path:path}")
async def delete_file(file_path: str):
    """Delete a file from the knowledge base."""
    full_path = Path(file_path)
    
    if not full_path.is_absolute():
        # Try relative to kb path
        full_path = get_kb_path() / file_path
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete file
    full_path.unlink()
    
    # Delete sidecar JSON if exists
    json_path = full_path.with_suffix('.json')
    if json_path.exists():
        json_path.unlink()
    
    return {"success": True, "deleted": str(full_path)}

@router.get("/search")
async def search_knowledge_base(
    q: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results")
):
    """Search the knowledge base."""
    kb_path = get_kb_path()
    
    if not kb_path.exists():
        return {"results": [], "total": 0, "query": q}
    
    results = []
    
    # Search in each category
    search_categories = [category] if category else [
        item.name for item in kb_path.iterdir() if item.is_dir()
    ]
    
    for cat_name in search_categories:
        category_path = get_category_path(cat_name)
        if not category_path.exists():
            continue
        
        for file_path in category_path.iterdir():
            if file_path.is_file() and file_path.suffix == '.md':
                try:
                    content = read_file_content(file_path)
                    frontmatter = parse_frontmatter(content)
                    
                    # Simple keyword matching
                    query_lower = q.lower()
                    content_lower = content.lower()
                    
                    # Check title, content, tags, categories
                    title = frontmatter.get('title', '')
                    tags = frontmatter.get('tags', [])
                    categories = frontmatter.get('categories', [])
                    
                    score = 0
                    if query_lower in title.lower():
                        score += 3
                    if query_lower in content_lower:
                        score += 1
                    if any(query_lower in tag.lower() for tag in tags):
                        score += 2
                    if any(query_lower in cat.lower() for cat in categories):
                        score += 2
                    
                    if score > 0:
                        results.append({
                            "path": str(file_path),
                            "filename": file_path.name,
                            "category": cat_name,
                            "title": title,
                            "content_snippet": content[:200] + "..." if len(content) > 200 else content,
                            "tags": tags,
                            "categories": categories,
                            "score": score,
                            "created_at": frontmatter.get('created_at'),
                            "author": frontmatter.get('author')
                        })
                except Exception as e:
                    # Skip files that can't be read
                    continue
    
    # Sort by score descending
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # Return top results
    return {
        "results": results[:limit],
        "total": len(results),
        "query": q
    }

@router.get("/recent")
async def get_recent_items(limit: int = Query(10, ge=1, le=100)):
    """Get recently added items."""
    kb_path = get_kb_path()
    
    if not kb_path.exists():
        return {"items": [], "total": 0}
    
    items = []
    
    for item in kb_path.iterdir():
        if item.is_dir():
            for file_path in item.iterdir():
                if file_path.is_file() and file_path.suffix == '.md':
                    try:
                        content = read_file_content(file_path)
                        frontmatter = parse_frontmatter(content)
                        
                        items.append({
                            "path": str(file_path),
                            "filename": file_path.name,
                            "category": item.name,
                            "title": frontmatter.get('title', file_path.stem),
                            "created_at": frontmatter.get('created_at'),
                            "processed_at": frontmatter.get('processed_at'),
                            "author": frontmatter.get('author'),
                            "tags": frontmatter.get('tags', [])
                        })
                    except:
                        continue
    
    # Sort by created_at or processed_at descending
    items.sort(key=lambda x: x.get('processed_at') or x.get('created_at') or '', reverse=True)
    
    return {
        "items": items[:limit],
        "total": len(items)
    }

@router.post("/categories")
async def create_category(name: str):
    """Create a new category."""
    category_path = get_category_path(name)
    
    if category_path.exists():
        raise HTTPException(status_code=400, detail=f"Category '{name}' already exists")
    
    category_path.mkdir(parents=True)
    
    # Initialize category with index.md
    index_path = category_path / "INDEX.md"
    with open(index_path, 'w') as f:
        f.write(f"# {name}\n\n")
    
    return {
        "success": True,
        "name": name,
        "path": str(category_path)
    }

@router.delete("/categories/{category}")
async def delete_category(category: str):
    """Delete a category and all its contents."""
    category_path = get_category_path(category)
    
    if not category_path.exists():
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")
    
    # Delete entire directory
    shutil.rmtree(category_path)
    
    return {"success": True, "deleted": category}

# =============================================================================
# Integration with Knowledge Base Python Module
# =============================================================================

@router.post("/sync")
async def sync_knowledge_base():
    """Sync knowledge base using Python module."""
    try:
        # Import and run the Python module
        import subprocess
        result = subprocess.run(
            ['python3', '-m', 'kb_core.orchestrator'],
            cwd='/Users/aijenquist/workspace/personal-kb',
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
