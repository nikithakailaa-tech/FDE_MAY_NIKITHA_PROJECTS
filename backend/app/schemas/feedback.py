from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class FeedbackCreate(BaseModel):
    complaint_id: int
    rating: int  # 1 to 5
    comments: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: int
    complaint_id: int
    customer_id: int
    rating: int
    comments: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True