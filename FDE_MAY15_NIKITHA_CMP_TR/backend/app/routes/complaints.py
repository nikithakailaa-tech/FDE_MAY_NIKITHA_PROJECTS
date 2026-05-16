from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.complaint import Complaint, ComplaintHistory
from app.models.notification import Notification
from app.models.user import User
from app.schemas.complaint import ComplaintCreate, ComplaintUpdate, ComplaintResponse, ComplaintHistoryResponse
from app.utils.dependencies import get_current_user, require_role
from datetime import datetime, timedelta
from typing import List
import random
import string

router = APIRouter(prefix="/complaints", tags=["Complaints"])

def generate_complaint_number():
    chars = string.ascii_uppercase + string.digits
    return "CMP-" + "".join(random.choices(chars, k=8))

def get_sla_deadline(priority: str):
    hours = {"low": 72, "medium": 48, "high": 24, "critical": 4}
    return datetime.utcnow() + timedelta(hours=hours.get(priority, 48))

def create_notification(db: Session, user_id: int, complaint_id: int, message: str, notif_type: str = "info"):
    notif = Notification(
        user_id=user_id,
        complaint_id=complaint_id,
        message=message,
        type=notif_type
    )
    db.add(notif)

@router.post("/", response_model=ComplaintResponse)
def create_complaint(
    data: ComplaintCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    complaint = Complaint(
        complaint_number=generate_complaint_number(),
        customer_id=current_user.id,
        category_id=data.category_id,
        title=data.title,
        description=data.description,
        priority=data.priority,
        status="open",
        sla_deadline=get_sla_deadline(data.priority)
    )
    db.add(complaint)
    db.flush()

    create_notification(
        db, current_user.id, complaint.id,
        f"Your complaint '{data.title}' has been registered. ID: {complaint.complaint_number}",
        "success"
    )

    # Notify admins/supervisors
    admins = db.query(User).filter(User.role.in_(["admin", "supervisor"])).all()
    for admin in admins:
        if admin.id != current_user.id:
            create_notification(
                db, admin.id, complaint.id,
                f"New complaint registered: {complaint.complaint_number} — {data.title} [{data.priority.upper()}]",
                "info"
            )

    db.commit()
    db.refresh(complaint)
    return complaint

@router.get("/", response_model=List[ComplaintResponse])
def get_complaints(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role == "customer":
        return db.query(Complaint).filter(Complaint.customer_id == current_user.id).order_by(Complaint.created_at.desc()).all()
    elif current_user.role == "agent":
        return db.query(Complaint).filter(Complaint.agent_id == current_user.id).order_by(Complaint.created_at.desc()).all()
    return db.query(Complaint).order_by(Complaint.created_at.desc()).all()

@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint

@router.put("/{complaint_id}", response_model=ComplaintResponse)
def update_complaint(
    complaint_id: int,
    data: ComplaintUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    old_status = complaint.status
    role = current_user.role

    # Role-based status transition rules
    if data.status and data.status != old_status:
        if role == "customer":
            raise HTTPException(status_code=403, detail="Customers cannot change complaint status")

        if role == "agent":
            # Agent can only work on their assigned complaints
            if complaint.agent_id != current_user.id:
                raise HTTPException(status_code=403, detail="You can only update complaints assigned to you")
            # If escalated, agent can pull it back to assigned to work on it
            allowed = {
                "open": ["in_progress"],
                "in_progress": ["resolved", "escalated"],
                "assigned": ["in_progress", "resolved", "escalated"],
                "escalated": ["assigned", "in_progress"],  # agent can reclaim escalated complaint
            }
            if data.status not in allowed.get(old_status, []):
                raise HTTPException(
                    status_code=403,
                    detail=f"Agent cannot change status from '{old_status}' to '{data.status}'"
                )

        # supervisor/admin (customer support) can change any status freely
        # including taking over escalated complaints

    if data.status:
        complaint.status = data.status
        # When agent reclaims an escalated complaint, re-assign to them
        if old_status == "escalated" and data.status == "assigned" and role == "agent":
            complaint.agent_id = current_user.id
    if data.agent_id:
        complaint.agent_id = data.agent_id
    if data.resolution_note:
        complaint.resolution_note = data.resolution_note
    if data.priority:
        complaint.priority = data.priority

    if data.status == "resolved":
        complaint.resolved_at = datetime.utcnow()

    history = ComplaintHistory(
        complaint_id=complaint.id,
        updated_by=current_user.id,
        old_status=old_status,
        new_status=complaint.status,
        note=data.resolution_note
    )
    db.add(history)

    # Notifications on status change
    if data.status and data.status != old_status:
        notif_type = "success" if data.status == "resolved" else ("warning" if data.status == "escalated" else "info")
        # Notify the customer
        create_notification(
            db, complaint.customer_id, complaint.id,
            f"Your complaint {complaint.complaint_number} status changed: {old_status.replace('_',' ').title()} → {data.status.replace('_',' ').title()}",
            notif_type
        )
        # Notify assigned agent if different from updater
        if complaint.agent_id and complaint.agent_id != current_user.id:
            create_notification(
                db, complaint.agent_id, complaint.id,
                f"Complaint {complaint.complaint_number} status updated to {data.status.replace('_',' ').title()}",
                notif_type
            )

    # Notify agent when assigned
    if data.agent_id and data.agent_id != complaint.agent_id:
        create_notification(
            db, data.agent_id, complaint.id,
            f"Complaint {complaint.complaint_number} has been assigned to you: {complaint.title}",
            "info"
        )

    db.commit()
    db.refresh(complaint)
    return complaint

@router.get("/{complaint_id}/history", response_model=List[ComplaintHistoryResponse])
def get_complaint_history(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return db.query(ComplaintHistory).filter(ComplaintHistory.complaint_id == complaint_id).all()
