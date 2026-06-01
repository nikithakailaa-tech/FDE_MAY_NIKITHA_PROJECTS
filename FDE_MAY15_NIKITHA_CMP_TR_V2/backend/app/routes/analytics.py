import sqlite3, os
from fastapi import APIRouter, HTTPException
from typing import Any

router = APIRouter(prefix="/analytics", tags=["Analytics"])

ANALYTICS_DB = os.path.join(
    os.path.dirname(__file__), "..", "..", "analytics.db"
)

def query(sql: str, params: tuple = ()) -> list[dict]:
    if not os.path.exists(ANALYTICS_DB):
        raise HTTPException(
            status_code=503,
            detail="Analytics DB not found. Run the ETL pipeline first."
        )
    conn = sqlite3.connect(ANALYTICS_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/sla-breach")
def sla_breach_report() -> Any:
    rows = query("""
        SELECT category, priority, total, breached, breach_rate
        FROM report_sla_breach
        ORDER BY breach_rate DESC
    """)
    total    = sum(r["total"]    for r in rows)
    breached = sum(r["breached"] for r in rows)
    return {
        "summary": {"total": total, "breached": breached,
                    "breach_rate": round(breached * 100.0 / total, 2) if total else 0},
        "by_category_priority": rows
    }


@router.get("/category-analysis")
def category_analysis() -> Any:
    return query("""
        SELECT category, total, resolved,
               ROUND(resolved*100.0/total, 2) as resolution_rate,
               avg_resolution_hours
        FROM report_category_analysis
        ORDER BY total DESC
    """)


@router.get("/monthly-trends")
def monthly_trends() -> Any:
    return query("""
        SELECT month_label, total, resolved, breached
        FROM report_monthly_trends
        ORDER BY rowid
    """)


@router.get("/agent-performance")
def agent_performance() -> Any:
    return query("""
        SELECT agent, assigned, resolved,
               ROUND(resolved*100.0/assigned, 2) as resolution_rate,
               avg_resolution_hours, sla_breached
        FROM report_agent_performance
        ORDER BY resolved DESC
    """)


@router.get("/summary")
def analytics_summary() -> Any:
    rows = query("SELECT COUNT(*) as total, SUM(sla_breached) as breached FROM analytics_complaints")
    r = rows[0]
    cat = query("SELECT COUNT(DISTINCT category) as c FROM analytics_complaints")[0]["c"]
    agents = query("SELECT COUNT(DISTINCT agent) as a FROM analytics_complaints")[0]["a"]
    return {
        "total_records": r["total"],
        "sla_breached":  r["breached"],
        "categories":    cat,
        "agents":        agents
    }
