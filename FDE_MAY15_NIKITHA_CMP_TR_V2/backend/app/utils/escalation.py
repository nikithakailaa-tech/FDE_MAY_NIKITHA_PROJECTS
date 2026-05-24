from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.complaint import Complaint
from app.models.notification import Notification


def run_escalation_check():
    db: Session = SessionLocal()
    try:
        now = datetime.utcnow()
        breached = db.query(Complaint).filter(
            Complaint.sla_deadline != None,
            Complaint.sla_deadline < now,
            Complaint.status.notin_(["resolved", "closed"])
        ).all()

        for complaint in breached:
            if complaint.status != "escalated":
                old_status = complaint.status
                complaint.status = "escalated"
                complaint.updated_at = now

                notif_msg = f"Complaint #{complaint.complaint_number} has been auto-escalated due to SLA breach."
                targets = set()
                if complaint.customer_id:
                    targets.add(complaint.customer_id)
                if complaint.agent_id:
                    targets.add(complaint.agent_id)

                from sqlalchemy import text
                supervisors = db.execute(
                    text("SELECT id FROM users WHERE role IN ('admin','supervisor') AND is_active = 1")
                ).fetchall()
                for row in supervisors:
                    targets.add(row[0])

                for uid in targets:
                    db.add(Notification(
                        user_id=uid,
                        complaint_id=complaint.id,
                        message=notif_msg,
                        type="sla_breach"
                    ))

        db.commit()
    finally:
        db.close()
