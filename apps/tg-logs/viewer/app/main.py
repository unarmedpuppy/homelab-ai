import os, sqlite3, math
from fastapi import FastAPI, Request, Query
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

DB_PATH = os.getenv("DB_PATH", "/app/data/messages.sqlite")
DATA_DIR = Path("/app/data")

app = FastAPI()
app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")

templates = Environment(
    loader=FileSystemLoader(str(Path(__file__).parent / "templates")),
    autoescape=select_autoescape(["html", "xml"])
)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
def root():
    return RedirectResponse("/channels")

@app.get("/channels")
def channels():
    """List all available channels"""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT c.id, c.name, c.username, c.title, c.description,
               COUNT(m.id) as message_count,
               COUNT(md.message_id) as media_count
        FROM channels c
        LEFT JOIN messages m ON c.id = m.channel_id
        LEFT JOIN media md ON c.id = md.channel_id AND m.id = md.message_id
        GROUP BY c.id, c.name, c.username, c.title, c.description
        ORDER BY c.title
    """)
    
    channels = []
    for row in cur.fetchall():
        channels.append({
            "id": row["id"],
            "name": row["name"],
            "username": row["username"],
            "title": row["title"],
            "description": row["description"],
            "message_count": row["message_count"],
            "media_count": row["media_count"]
        })
    
    conn.close()
    
    tmpl = templates.get_template("channels.html")
    return tmpl.render(channels=channels)

@app.get("/messages")
def messages(
    request: Request,
    channel_id: str = Query(default="", description="Channel ID to filter by"),
    q: str = Query(default="", description="Full-text search"),
    has_media: int = Query(default=0, ge=0, le=1),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    sort: str = Query(default="desc", regex="^(asc|desc)$")
):
    conn = get_db()
    cur = conn.cursor()

    filters = []
    params = []

    if channel_id:
        filters.append("m.channel_id = ?")
        params.append(channel_id)

    if q:
        filters.append("(m.text LIKE ?)")
        params.append(f"%{q}%")

    if has_media:
        filters.append("EXISTS (SELECT 1 FROM media md WHERE md.message_id = m.id AND md.channel_id = m.channel_id)")

    where_clause = ("WHERE " + " AND ".join(filters)) if filters else ""

    count_sql = f"SELECT COUNT(*) FROM messages m {where_clause}"
    total = cur.execute(count_sql, params).fetchone()[0]

    order = "ASC" if sort == "asc" else "DESC"
    offset = (page - 1) * per_page

    sql = f"""
    SELECT m.id, m.channel_id, m.date, m.sender_id, m.text,
           c.title as channel_title, c.username as channel_username,
           (SELECT file_path FROM media md WHERE md.message_id = m.id AND md.channel_id = m.channel_id) as file_path,
           (SELECT mime_type FROM media md WHERE md.message_id = m.id AND md.channel_id = m.channel_id) as mime_type
    FROM messages m
    LEFT JOIN channels c ON m.channel_id = c.id
    {where_clause}
    ORDER BY m.id {order}
    LIMIT ? OFFSET ?
    """
    rows = cur.execute(sql, params + [per_page, offset]).fetchall()
    conn.close()

    # Map absolute/relative paths for StaticFiles at /data
    def to_data_url(path):
        if not path:
            return None
        p = Path(path)
        # If DB stored "data/..." use as-is; else make it relative to /app/data
        return "/data/" + str(p).replace("\\", "/").split("data/", 1)[-1]

    items = []
    for r in rows:
        items.append({
            "id": r["id"],
            "channel_id": r["channel_id"],
            "channel_title": r["channel_title"],
            "channel_username": r["channel_username"],
            "date": r["date"],
            "sender_id": r["sender_id"],
            "text": r["text"] or "",
            "media_url": to_data_url(r["file_path"]),
            "mime_type": r["mime_type"]
        })

    total_pages = max(1, math.ceil(total / per_page))

    # Get list of channels for the template
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, title, username FROM channels ORDER BY title")
    channels = [{"id": row["id"], "title": row["title"], "username": row["username"]} for row in cur.fetchall()]
    conn.close()

    tmpl = templates.get_template("index.html")
    return tmpl.render(
        request=request,
        items=items,
        channels=channels,
        selected_channel_id=channel_id,
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        q=q,
        has_media=has_media,
        sort=sort
    )

