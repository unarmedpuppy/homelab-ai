"""
Metrics module for usage analytics and dashboard data.
Tracks requests, token usage, model performance, and activity patterns.
"""
import logging
import json
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

from database import get_db_connection
from models import MetricCreate, Metric, DailyStats, ActivityDay, ModelUsage, DashboardStats

logger = logging.getLogger(__name__)


# ============================================================================
# Metric Logging
# ============================================================================

def log_metric(metric: MetricCreate) -> Metric:
    """Log a single metric record."""
    now = datetime.now(timezone.utc)
    date = now.date()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO metrics
            (timestamp, date, conversation_id, session_id, endpoint,
             model_requested, model_used, backend, prompt_tokens,
             completion_tokens, total_tokens, duration_ms, success,
             error, streaming, tool_calls_count, user_id, project, cost_usd)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now,
                date,
                metric.conversation_id,
                metric.session_id,
                metric.endpoint,
                metric.model_requested,
                metric.model_used,
                metric.backend,
                metric.prompt_tokens,
                metric.completion_tokens,
                metric.total_tokens,
                metric.duration_ms,
                metric.success,
                metric.error,
                metric.streaming,
                metric.tool_calls_count,
                metric.user_id,
                metric.project,
                metric.cost_usd,
            ),
        )
        metric_id = cursor.lastrowid
        conn.commit()

    logger.debug(f"Logged metric {metric_id}")
    return get_metric(metric_id)


def get_metric(metric_id: int) -> Optional[Metric]:
    """Get a metric by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM metrics WHERE id = ?", (metric_id,))
        row = cursor.fetchone()

    if not row:
        return None

    return _row_to_metric(row)


# ============================================================================
# Query Functions
# ============================================================================

def get_metrics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    backend: Optional[str] = None,
    user_id: Optional[str] = None,
    project: Optional[str] = None,
    limit: int = 1000,
) -> List[Metric]:
    """Query metrics with filters."""
    query = "SELECT * FROM metrics WHERE 1=1"
    params = []

    if start_date:
        query += " AND timestamp >= ?"
        params.append(start_date)

    if end_date:
        query += " AND timestamp <= ?"
        params.append(end_date)

    if backend:
        query += " AND backend = ?"
        params.append(backend)

    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)

    if project:
        query += " AND project = ?"
        params.append(project)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

    return [_row_to_metric(row) for row in rows]


# ============================================================================
# Aggregation Functions
# ============================================================================

def get_daily_activity(days: int = 365) -> List[ActivityDay]:
    """
    Get daily activity for GitHub-style contribution chart.

    Returns activity levels:
    - 0: No activity
    - 1: 1-5 requests
    - 2: 6-15 requests
    - 3: 16-30 requests
    - 4: 31+ requests
    """
    start_date = datetime.now(timezone.utc).date() - timedelta(days=days)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT date, COUNT(*) as count
            FROM metrics
            WHERE date >= ?
            GROUP BY date
            ORDER BY date ASC
            """,
            (start_date,)
        )
        rows = cursor.fetchall()

    activity = []
    for row in rows:
        count = row["count"]

        # Calculate activity level
        if count == 0:
            level = 0
        elif count <= 5:
            level = 1
        elif count <= 15:
            level = 2
        elif count <= 30:
            level = 3
        else:
            level = 4

        activity.append(
            ActivityDay(
                date=row["date"],
                count=count,
                level=level,
            )
        )

    return activity


def get_model_usage(days: Optional[int] = None) -> List[ModelUsage]:
    """Get model usage statistics."""
    query = """
        SELECT
            model_used as model,
            COUNT(*) as count,
            SUM(total_tokens) as total_tokens
        FROM metrics
        WHERE model_used IS NOT NULL
    """
    params = []

    if days:
        start_date = datetime.now(timezone.utc).date() - timedelta(days=days)
        query += " AND date >= ?"
        params.append(start_date)

    query += " GROUP BY model_used ORDER BY count DESC"

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

    total_count = sum(row["count"] for row in rows)

    usage = []
    for row in rows:
        count = row["count"]
        percentage = (count / total_count * 100) if total_count > 0 else 0

        usage.append(
            ModelUsage(
                model=row["model"] or "unknown",
                count=count,
                percentage=round(percentage, 2),
                total_tokens=row["total_tokens"] or 0,
            )
        )

    return usage


def get_provider_distribution(days: Optional[int] = None) -> Dict[str, float]:
    """
    Get provider distribution (Local vs OpenCode).

    Returns:
        {"local": 72.5, "opencode": 27.5}
    """
    query = """
        SELECT
            CASE
                WHEN backend LIKE 'opencode%' THEN 'opencode'
                ELSE 'local'
            END as provider,
            COUNT(*) as count
        FROM metrics
        WHERE backend IS NOT NULL
    """
    params = []

    if days:
        start_date = datetime.now(timezone.utc).date() - timedelta(days=days)
        query += " AND date >= ?"
        params.append(start_date)

    query += " GROUP BY provider"

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

    total_count = sum(row["count"] for row in rows)
    distribution = {}

    for row in rows:
        count = row["count"]
        percentage = (count / total_count * 100) if total_count > 0 else 0
        distribution[row["provider"]] = round(percentage, 2)

    return distribution


def calculate_streak() -> int:
    """Calculate longest consecutive days of activity."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT date FROM metrics ORDER BY date ASC
            """
        )
        rows = cursor.fetchall()

    if not rows:
        return 0

    dates = [datetime.fromisoformat(row["date"]).date() for row in rows]

    max_streak = 1
    current_streak = 1

    for i in range(1, len(dates)):
        diff = (dates[i] - dates[i - 1]).days

        if diff == 1:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 1

    return max_streak


def get_dashboard_stats() -> DashboardStats:
    """
    Get complete dashboard statistics (OpenCode Wrapped style).
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Started date (first metric)
        cursor.execute("SELECT MIN(date) FROM metrics")
        started_date = cursor.fetchone()[0] or datetime.now(timezone.utc).date().isoformat()

        # Days active (unique dates with activity)
        cursor.execute("SELECT COUNT(DISTINCT date) FROM metrics")
        days_active = cursor.fetchone()[0]

        # Most active day
        cursor.execute(
            """
            SELECT date, COUNT(*) as count
            FROM metrics
            GROUP BY date
            ORDER BY count DESC
            LIMIT 1
            """
        )
        most_active_row = cursor.fetchone()
        most_active_day = most_active_row["date"] if most_active_row else started_date
        most_active_day_count = most_active_row["count"] if most_active_row else 0

        # Total sessions (unique session_ids)
        cursor.execute(
            """
            SELECT COUNT(DISTINCT session_id) FROM metrics
            WHERE session_id IS NOT NULL
            """
        )
        total_sessions = cursor.fetchone()[0]

        # Total messages
        cursor.execute("SELECT COUNT(*) FROM metrics")
        total_messages = cursor.fetchone()[0]

        # Total tokens
        cursor.execute("SELECT SUM(total_tokens) FROM metrics")
        total_tokens = cursor.fetchone()[0] or 0

        # Unique projects
        cursor.execute(
            """
            SELECT COUNT(DISTINCT project) FROM metrics
            WHERE project IS NOT NULL
            """
        )
        unique_projects = cursor.fetchone()[0]

    # Get activity chart (last 365 days)
    activity_chart = get_daily_activity(days=365)

    # Get top models
    top_models = get_model_usage()[:5]  # Top 5 models

    # Get provider distribution
    providers_used = get_provider_distribution()

    # Calculate longest streak
    longest_streak = calculate_streak()

    # Calculate cost savings (OpenCode Zen)
    # Rough estimate: Claude API costs ~$3 per million tokens
    # OpenCode subscription is flat fee, so all usage is "savings"
    opencode_tokens = sum(
        m.total_tokens for m in get_metrics()
        if m.backend and m.backend.startswith("opencode")
    )
    estimated_api_cost = (opencode_tokens / 1_000_000) * 3.0
    cost_savings = round(estimated_api_cost, 2) if opencode_tokens > 0 else None

    return DashboardStats(
        started_date=started_date,
        days_active=days_active,
        most_active_day=most_active_day,
        most_active_day_count=most_active_day_count,
        activity_chart=activity_chart,
        top_models=top_models,
        providers_used=providers_used,
        total_sessions=total_sessions,
        total_messages=total_messages,
        total_tokens=total_tokens,
        unique_projects=unique_projects,
        longest_streak=longest_streak,
        cost_savings=cost_savings,
    )


# ============================================================================
# Daily Stats Materialization
# ============================================================================

def update_daily_stats(date: Optional[str] = None):
    """
    Update materialized daily stats for a specific date.

    If date is None, updates stats for yesterday (complete day).
    """
    if date is None:
        date = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Aggregate metrics for the date
        cursor.execute(
            """
            SELECT
                COUNT(*) as total_requests,
                COUNT(DISTINCT conversation_id) as unique_conversations,
                COUNT(DISTINCT session_id) as unique_sessions,
                SUM(total_tokens) as total_tokens,
                AVG(duration_ms) as avg_duration_ms,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate
            FROM metrics
            WHERE date = ?
            """,
            (date,)
        )
        agg = cursor.fetchone()

        # Get messages count (could be different from requests if batched)
        cursor.execute(
            """
            SELECT COUNT(*) FROM messages
            WHERE DATE(timestamp) = ?
            """,
            (date,)
        )
        total_messages = cursor.fetchone()[0]

        # Get models used
        cursor.execute(
            """
            SELECT model_used, COUNT(*) as count
            FROM metrics
            WHERE date = ? AND model_used IS NOT NULL
            GROUP BY model_used
            """,
            (date,)
        )
        models_rows = cursor.fetchall()
        models_used = {row["model_used"]: row["count"] for row in models_rows}

        # Get backends used
        cursor.execute(
            """
            SELECT backend, COUNT(*) as count
            FROM metrics
            WHERE date = ? AND backend IS NOT NULL
            GROUP BY backend
            """,
            (date,)
        )
        backends_rows = cursor.fetchall()
        backends_used = {row["backend"]: row["count"] for row in backends_rows}

        # Upsert daily stats
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_stats
            (date, total_requests, total_messages, total_tokens,
             unique_conversations, unique_sessions, models_used,
             backends_used, avg_duration_ms, success_rate, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                date,
                agg["total_requests"],
                total_messages,
                agg["total_tokens"] or 0,
                agg["unique_conversations"],
                agg["unique_sessions"],
                json.dumps(models_used),
                json.dumps(backends_used),
                agg["avg_duration_ms"] or 0,
                agg["success_rate"] or 0,
                datetime.now(timezone.utc),
            ),
        )
        conn.commit()

    logger.info(f"Updated daily stats for {date}")


def get_daily_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 365,
) -> List[DailyStats]:
    """Get daily stats with optional date range."""
    query = "SELECT * FROM daily_stats WHERE 1=1"
    params = []

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date DESC LIMIT ?"
    params.append(limit)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

    return [_row_to_daily_stats(row) for row in rows]


# ============================================================================
# Helper Functions
# ============================================================================

def _row_to_metric(row: Any) -> Metric:
    """Convert database row to Metric model."""
    return Metric(
        id=row["id"],
        timestamp=datetime.fromisoformat(row["timestamp"]),
        date=row["date"],
        conversation_id=row["conversation_id"],
        session_id=row["session_id"],
        endpoint=row["endpoint"],
        model_requested=row["model_requested"],
        model_used=row["model_used"],
        backend=row["backend"],
        prompt_tokens=row["prompt_tokens"],
        completion_tokens=row["completion_tokens"],
        total_tokens=row["total_tokens"],
        duration_ms=row["duration_ms"],
        success=bool(row["success"]),
        error=row["error"],
        streaming=bool(row["streaming"]),
        tool_calls_count=row["tool_calls_count"],
        user_id=row["user_id"],
        project=row["project"],
    )


def _row_to_daily_stats(row: Any) -> DailyStats:
    """Convert database row to DailyStats model."""
    return DailyStats(
        date=row["date"],
        total_requests=row["total_requests"],
        total_messages=row["total_messages"],
        total_tokens=row["total_tokens"],
        unique_conversations=row["unique_conversations"],
        unique_sessions=row["unique_sessions"],
        models_used=json.loads(row["models_used"]) if row["models_used"] else {},
        backends_used=json.loads(row["backends_used"]) if row["backends_used"] else {},
        avg_duration_ms=row["avg_duration_ms"],
        success_rate=row["success_rate"],
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


if __name__ == "__main__":
    # Test the metrics module
    logging.basicConfig(level=logging.INFO)

    # Log test metric
    metric = log_metric(
        MetricCreate(
            endpoint="/v1/chat/completions",
            model_requested="auto",
            model_used="3090",
            backend="3090",
            prompt_tokens=50,
            completion_tokens=100,
            total_tokens=150,
            duration_ms=1200,
            success=True,
            streaming=False,
        )
    )
    print(f"Logged metric: {metric.id}")

    # Get model usage
    usage = get_model_usage()
    print(f"\nModel usage: {usage}")

    # Get dashboard stats
    stats = get_dashboard_stats()
    print(f"\nDashboard stats:")
    print(f"  Started: {stats.started_date}")
    print(f"  Days active: {stats.days_active}")
    print(f"  Total messages: {stats.total_messages}")
    print(f"  Total tokens: {stats.total_tokens}")
    print(f"  Top models: {stats.top_models}")
