from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    complaint_number = Column(String, unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"))
    agent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String, default="medium")
    status = Column(String, default="open")
    resolution_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    sla_deadline = Column(DateTime, nullable=True)

    customer = relationship("User", back_populates="complaints", foreign_keys=[customer_id])
    agent = relationship("User", back_populates="assigned_complaints", foreign_keys=[agent_id])
    category = relationship("Category", back_populates="complaints")
    history = relationship("ComplaintHistory", back_populates="complaint")
    attachments = relationship("Attachment", back_populates="complaint")
    feedback = relationship("Feedback", back_populates="complaint")

    @property
    def customer_name(self):
        return self.customer.name if self.customer else None

    @property
    def customer_email(self):
        return self.customer.email if self.customer else None

    @property
    def agent_name(self):
        return self.agent.name if self.agent else None

    @property
    def category_name(self):
        return self.category.name if self.category else None


class ComplaintHistory(Base):
    __tablename__ = "complaint_history"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))
    old_status = Column(String)
    new_status = Column(String)
    note = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint", back_populates="history")
    updater = relationship("User", foreign_keys=[updated_by])

    @property
    def updated_by_name(self):
        return self.updater.name if self.updater else None
