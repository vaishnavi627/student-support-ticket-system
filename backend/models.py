from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    role = Column(String(30), nullable=False, default="STUDENT")
    department = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True)
    ticket_number = Column(String(30), unique=True, nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"))
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(80), default="Other")
    priority = Column(String(10), default="P3")
    status = Column(String(40), default="NEW")
    department = Column(String(100), default="Student Services")
    ai_summary = Column(Text)
    ai_reason = Column(Text)
    ai_confidence = Column(Float)
    sla_hours = Column(Integer, default=72)
    sla_deadline = Column(DateTime)
    pending_action = Column(Text)
    pending_party = Column(String(30))
    resolution_summary = Column(Text)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TicketActivity(Base):
    __tablename__ = "ticket_activities"
    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    actor_name = Column(String(120), nullable=False)
    action = Column(String(100), nullable=False)
    old_value = Column(String(500))
    new_value = Column(String(500))
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
