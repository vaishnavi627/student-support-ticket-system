from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class TicketCreate(BaseModel):
    student_name: str = Field(min_length=2)
    student_email: str = Field(min_length=5)
    title: str = Field(min_length=3)
    description: str = Field(min_length=5)

class TicketOut(BaseModel):
    id: int
    ticket_number: str
    title: str
    description: str
    category: str
    priority: str
    status: str
    department: str
    ai_summary: Optional[str] = None
    ai_reason: Optional[str] = None
    ai_confidence: Optional[float] = None
    sla_hours: int
    sla_deadline: Optional[datetime] = None
    pending_action: Optional[str] = None
    pending_party: Optional[str] = None
    resolution_summary: Optional[str] = None
    assigned_to: Optional[int] = None
    created_at: datetime
    class Config:
        from_attributes = True

class StatusUpdate(BaseModel):
    status: str
    comment: Optional[str] = None

class AssignUpdate(BaseModel):
    staff_name: str
    staff_email: str
    department: str

class PriorityUpdate(BaseModel):
    priority: str
    reason: str = Field(min_length=3)

class StaffMessage(BaseModel):
    actor_name: str
    message: str = Field(min_length=2)

class ResolveRequest(BaseModel):
    actor_name: str
    resolution_note: Optional[str] = None

class ActivityOut(BaseModel):
    id: int
    actor_name: str
    action: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    comment: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True
