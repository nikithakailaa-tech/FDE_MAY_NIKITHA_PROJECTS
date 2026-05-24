from pydantic import BaseModel
from datetime import datetime

class AttachmentResponse(BaseModel):
    id: int
    complaint_id: int
    file_name: str
    file_path: str
    uploaded_at: datetime

    class Config:
        from_attributes = True
