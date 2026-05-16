from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.feedback import Feedback
from app.models.complaint import Complaint
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.utils.dependencies import get_current_user
from typing import List

router = APIRouter(prefix="/feedback", tags=["Feedback"])

@router.post("/", response_model=FeedbackResponse)
def submit_feedback(
    data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    complaint = db.query(Complaint).filter(Complaint.id == data.complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    if complaint.status != "resolved":
        raise HTTPException(status_code=400, detail="Can only give feedback on resolved complaints")
    
    if data.rating < 1 or data.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    existing = db.query(Feedback).filter(
        Feedback.complaint_id == data.complaint_id,
        Feedback.customer_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Feedback already submitted")

    feedback = Feedback(
        complaint_id=data.complaint_id,
        customer_id=current_user.id,
        rating=data.rating,
        comments=data.comments
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback

@router.get("/", response_model=List[FeedbackResponse])
def get_all_feedback(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return db.query(Feedback).all()