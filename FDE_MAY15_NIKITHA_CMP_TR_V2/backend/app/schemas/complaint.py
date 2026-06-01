from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ComplaintCreate(BaseModel):
    title: str
    description: str
    category_id: int
    priority: str = "medium"

class ComplaintUpdate(BaseModel):
    status: Optional[str] = None
    agent_id: Optional[int] = None
    resolution_note: Optional[str] = None
    priority: Optional[str] = None

class ComplaintResponse(BaseModel):
    id: int
    complaint_number: str
    title: str
    description: str
    priority: str
    status: str
    category_id: int
    category_name: Optional[str] = None
    customer_id: int
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    agent_id: Optional[int] = None
    agent_name: Optional[str] = None
    resolution_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    sla_deadline: Optional[datetime] = None

    class Config:
        from_attributes = True

class ComplaintHistoryResponse(BaseModel):
    id: int
    complaint_id: int
    updated_by: int
    updated_by_name: Optional[str] = None
    old_status: str
    new_status: str
    note: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True
