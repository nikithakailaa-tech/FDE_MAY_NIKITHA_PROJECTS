from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.complaint import Complaint
from app.models.feedback import Feedback
from app.models.category import Category
from app.models.user import User
from app.utils.dependencies import get_current_user
from datetime import datetime, timedelta

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    q = db.query(Complaint)
    if current_user.role == "customer":
        q = q.filter(Complaint.customer_id == current_user.id)
    elif current_user.role == "agent":
        q = q.filter(Complaint.agent_id == current_user.id)

    total = q.count()
    open_c = q.filter(Complaint.status == "open").count()
    in_progress = q.filter(Complaint.status == "in_progress").count()
    resolved = q.filter(Complaint.status == "resolved").count()
    closed = q.filter(Complaint.status == "closed").count()
    escalated = q.filter(Complaint.status == "escalated").count()
    pending = q.filter(Complaint.status == "pending").count()

    sla_breached = q.filter(
        Complaint.sla_deadline < datetime.utcnow(),
        Complaint.status.notin_(["resolved", "closed"])
    ).count()

    feedbacks = db.query(Feedback).all()
    avg_rating = round(sum(f.rating for f in feedbacks) / len(feedbacks), 2) if feedbacks else 0

    resolved_with_time = q.filter(
        Complaint.status.in_(["resolved", "closed"]),
        Complaint.resolved_at != None
    ).all()
    if resolved_with_time:
        total_seconds = sum(
            (c.resolved_at - c.created_at).total_seconds()
            for c in resolved_with_time
        )
        avg_hours = round(total_seconds / len(resolved_with_time) / 3600, 1)
    else:
        avg_hours = 0

    return {
        "total_complaints": total,
        "open": open_c,
        "in_progress": in_progress,
        "resolved": resolved,
        "closed": closed,
        "escalated": escalated,
        "pending": pending,
        "sla_breached": sla_breached,
        "average_rating": avg_rating,
        "avg_resolution_hours": avg_hours
    }

@router.get("/category-stats")
def get_category_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    results = (
        db.query(Category.name, func.count(Complaint.id))
        .outerjoin(Complaint, Category.id == Complaint.category_id)
        .group_by(Category.name)
        .all()
    )
    return [{"category": name, "count": count} for name, count in results]

@router.get("/agent-stats")
def get_agent_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    agents = db.query(User).filter(User.role == "agent").all()
    stats = []
    for agent in agents:
        assigned = db.query(Complaint).filter(Complaint.agent_id == agent.id).count()
        resolved = db.query(Complaint).filter(
            Complaint.agent_id == agent.id,
            Complaint.status == "resolved"
        ).count()
        stats.append({
            "agent": agent.name,
            "assigned": assigned,
            "resolved": resolved
        })
    return stats

@router.get("/monthly-trends")
def get_monthly_trends(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    months = []
    for i in range(5, -1, -1):
        start = datetime.utcnow().replace(day=1) - timedelta(days=30 * i)
        end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        count = db.query(Complaint).filter(
            Complaint.created_at >= start,
            Complaint.created_at < end
        ).count()
        months.append({"month": start.strftime("%b %Y"), "count": count})
    return months
