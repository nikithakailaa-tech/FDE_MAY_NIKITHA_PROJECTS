"""
ETL Pipeline - Phase 2
Extract complaint records from CSV -> Transform -> Load into analytics DB
"""

import csv
import sqlite3
import os
from datetime import datetime

CSV_PATH = os.path.join(os.path.dirname(__file__), "dataset", "complaints_dataset.csv")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "analytics.db")


# ─── EXTRACT ────────────────────────────────────────────────────────────────

def extract(csv_path: str) -> list[dict]:
    records = []
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            records.append(row)
    print(f"[EXTRACT] {len(records)} records read from {csv_path}")
    return records


# ─── TRANSFORM ──────────────────────────────────────────────────────────────

PRIORITY_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}
STATUS_GROUP  = {
    "open": "active", "in_progress": "active", "pending": "active",
    "escalated": "active", "resolved": "completed", "closed": "completed"
}

def transform(records: list[dict]) -> list[dict]:
    transformed = []
    for r in records:
        try:
            created_at = datetime.strptime(r["created_at"], "%Y-%m-%d %H:%M:%S")
            month_label = created_at.strftime("%b %Y")

            resolution_hours = float(r["resolution_hours"]) if r["resolution_hours"] else None
            sla_limit        = int(r["sla_limit_hours"])
            sla_breached     = r["sla_breached"].strip().lower() in ("true", "1", "yes")

            transformed.append({
                "complaint_id":    int(r["complaint_id"]),
                "title":           r["title"],
                "category":        r["category"].strip(),
                "priority":        r["priority"].strip().lower(),
                "priority_rank":   PRIORITY_RANK.get(r["priority"].strip().lower(), 0),
                "status":          r["status"].strip().lower(),
                "status_group":    STATUS_GROUP.get(r["status"].strip().lower(), "active"),
                "agent":           r["agent"].strip(),
                "created_at":      r["created_at"],
                "resolved_at":     r["resolved_at"] if r["resolved_at"] else None,
                "resolution_hours":resolution_hours,
                "sla_limit_hours": sla_limit,
                "sla_breached":    int(sla_breached),
                "month_label":     month_label,
            })
        except Exception as e:
            print(f"[TRANSFORM] Skipping row {r.get('complaint_id','?')}: {e}")

    breached = sum(1 for r in transformed if r["sla_breached"])
    print(f"[TRANSFORM] {len(transformed)} records transformed | SLA breached: {breached}")
    return transformed


# ─── LOAD ───────────────────────────────────────────────────────────────────

DDL = """
CREATE TABLE IF NOT EXISTS analytics_complaints (
    id               INTEGER PRIMARY KEY,
    complaint_id     INTEGER UNIQUE,
    title            TEXT,
    category         TEXT,
    priority         TEXT,
    priority_rank    INTEGER,
    status           TEXT,
    status_group     TEXT,
    agent            TEXT,
    created_at       TEXT,
    resolved_at      TEXT,
    resolution_hours REAL,
    sla_limit_hours  INTEGER,
    sla_breached     INTEGER,
    month_label      TEXT,
    loaded_at        TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS report_sla_breach (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category    TEXT,
    priority    TEXT,
    total       INTEGER,
    breached    INTEGER,
    breach_rate REAL,
    generated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS report_category_analysis (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    category     TEXT,
    total        INTEGER,
    resolved     INTEGER,
    avg_resolution_hours REAL,
    generated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS report_monthly_trends (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    month_label  TEXT,
    total        INTEGER,
    resolved     INTEGER,
    breached     INTEGER,
    generated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS report_agent_performance (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    agent                TEXT,
    assigned             INTEGER,
    resolved             INTEGER,
    avg_resolution_hours REAL,
    sla_breached         INTEGER,
    generated_at         TEXT DEFAULT (datetime('now'))
);
"""

def load(records: list[dict], db_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()

    for stmt in DDL.strip().split(";"):
        s = stmt.strip()
        if s:
            cur.execute(s)

    cur.execute("DELETE FROM analytics_complaints")
    cur.executemany("""
        INSERT OR REPLACE INTO analytics_complaints
        (complaint_id,title,category,priority,priority_rank,status,status_group,
         agent,created_at,resolved_at,resolution_hours,sla_limit_hours,sla_breached,month_label)
        VALUES
        (:complaint_id,:title,:category,:priority,:priority_rank,:status,:status_group,
         :agent,:created_at,:resolved_at,:resolution_hours,:sla_limit_hours,:sla_breached,:month_label)
    """, records)
    print(f"[LOAD] Loaded {len(records)} rows into analytics_complaints")

    # ── report_sla_breach ──
    cur.execute("DELETE FROM report_sla_breach")
    cur.execute("""
        INSERT INTO report_sla_breach (category, priority, total, breached, breach_rate)
        SELECT category, priority,
               COUNT(*) as total,
               SUM(sla_breached) as breached,
               ROUND(SUM(sla_breached)*100.0/COUNT(*), 2) as breach_rate
        FROM analytics_complaints
        GROUP BY category, priority
    """)

    # ── report_category_analysis ──
    cur.execute("DELETE FROM report_category_analysis")
    cur.execute("""
        INSERT INTO report_category_analysis (category, total, resolved, avg_resolution_hours)
        SELECT category,
               COUNT(*) as total,
               SUM(CASE WHEN status_group='completed' THEN 1 ELSE 0 END) as resolved,
               ROUND(AVG(CASE WHEN resolution_hours IS NOT NULL THEN resolution_hours END), 2)
        FROM analytics_complaints
        GROUP BY category
    """)

    # ── report_monthly_trends ──
    cur.execute("DELETE FROM report_monthly_trends")
    cur.execute("""
        INSERT INTO report_monthly_trends (month_label, total, resolved, breached)
        SELECT month_label,
               COUNT(*) as total,
               SUM(CASE WHEN status_group='completed' THEN 1 ELSE 0 END),
               SUM(sla_breached)
        FROM analytics_complaints
        GROUP BY month_label
        ORDER BY MIN(created_at)
    """)

    # ── report_agent_performance ──
    cur.execute("DELETE FROM report_agent_performance")
    cur.execute("""
        INSERT INTO report_agent_performance (agent, assigned, resolved, avg_resolution_hours, sla_breached)
        SELECT agent,
               COUNT(*) as assigned,
               SUM(CASE WHEN status_group='completed' THEN 1 ELSE 0 END) as resolved,
               ROUND(AVG(CASE WHEN resolution_hours IS NOT NULL THEN resolution_hours END), 2),
               SUM(sla_breached)
        FROM analytics_complaints
        GROUP BY agent
    """)

    conn.commit()
    conn.close()
    print(f"[LOAD] Reporting tables refreshed in {db_path}")


# ─── RUN ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("ETL PIPELINE — Phase 2 Complaint Analytics")
    print("=" * 50)
    raw        = extract(CSV_PATH)
    cleaned    = transform(raw)
    load(cleaned, DB_PATH)
    print("=" * 50)
    print("ETL complete.")
