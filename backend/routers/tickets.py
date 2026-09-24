from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Ticket, TicketActivity, User
from ..schemas import (
    ActivityOut,
    AssignUpdate,
    PriorityUpdate,
    ResolveRequest,
    StaffMessage,
    StatusUpdate,
    TicketCreate,
    TicketOut,
)
from ..services.llm_service import (
    analyze_ticket,
    create_resolution_summary,
    extract_pending_action,
    suggest_response,
)
from ..services.sla_service import calculate_deadline

router = APIRouter(prefix="/tickets", tags=["Tickets"])


def log_activity(db, ticket_id, actor, action, old=None, new=None, comment=None):
    """Record a ticket activity entry in the database."""
    db.add(
        TicketActivity(
            ticket_id=ticket_id,
            actor_name=actor,
            action=action,
            old_value=old,
            new_value=new,
            comment=comment,
        )
    )


@router.post("", response_model=TicketOut)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    """Create a new support ticket and run AI classification."""
    # Reuse existing student or create a new one
    student = db.query(User).filter(User.email == payload.student_email).first()
    if not student:
        student = User(
            name=payload.student_name,
            email=payload.student_email,
            role="STUDENT",
        )
        db.add(student)
        db.commit()
        db.refresh(student)

    # Run AI analysis
    ai = analyze_ticket(payload.title, payload.description)
    hours, deadline = calculate_deadline(ai["priority"])

    # Build the ticket
    ticket = Ticket(
        ticket_number="TEMP",
        student_id=student.id,
        title=payload.title,
        description=payload.description,
        category=ai.get("category", "Other"),
        priority=ai.get("priority", "P3"),
        status="NEW",
        department=ai.get("department", "Student Services"),
        ai_summary=ai.get("summary"),
        ai_reason=ai.get("reason"),
        ai_confidence=ai.get("confidence"),
        sla_hours=hours,
        sla_deadline=deadline,
    )
    db.add(ticket)
    db.flush()
    ticket.ticket_number = f"TKT-{ticket.id:05d}"

    log_activity(
        db, ticket.id, payload.student_name, "TICKET_CREATED",
        new="NEW", comment="Ticket created and analyzed by AI.",
    )
    log_activity(
        db, ticket.id, "AI", "AI_CLASSIFIED",
        new=f"{ticket.category} | {ticket.priority} | {ticket.department}",
        comment=ticket.ai_reason,
    )

    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("", response_model=list[TicketOut])
def list_tickets(db: Session = Depends(get_db)):
    """Return all tickets ordered by most recent first."""
    return db.query(Ticket).order_by(Ticket.created_at.desc()).all()


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Return a single ticket by ID."""
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.put("/{ticket_id}/assign", response_model=TicketOut)
def assign_ticket(ticket_id: int, payload: AssignUpdate, db: Session = Depends(get_db)):
    """Assign a ticket to a staff member."""
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Reuse existing staff user or create a new one
    staff = db.query(User).filter(User.email == payload.staff_email).first()
    if not staff:
        staff = User(
            name=payload.staff_name,
            email=payload.staff_email,
            role="STAFF",
            department=payload.department,
        )
        db.add(staff)
        db.commit()
        db.refresh(staff)

    old_status = ticket.status
    ticket.assigned_to = staff.id
    ticket.status = "ASSIGNED"

    log_activity(
        db, ticket.id, payload.staff_name, "ASSIGNED",
        old=old_status, new="ASSIGNED",
        comment=f"Assigned to {payload.staff_name} ({payload.department}).",
    )

    db.commit()
    db.refresh(ticket)
    return ticket


@router.put("/{ticket_id}/status", response_model=TicketOut)
def update_status(ticket_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    """Update the status of a ticket."""
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    old_status = ticket.status
    ticket.status = payload.status

    log_activity(
        db, ticket.id, "Staff", "STATUS_CHANGED",
        old=old_status, new=payload.status, comment=payload.comment,
    )

    db.commit()
    db.refresh(ticket)
    return ticket


@router.put("/{ticket_id}/priority", response_model=TicketOut)
def override_priority(ticket_id: int, payload: PriorityUpdate, db: Session = Depends(get_db)):
    """Override the AI-assigned priority of a ticket."""
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if payload.priority not in {"P1", "P2", "P3", "P4"}:
        raise HTTPException(status_code=400, detail="Invalid priority. Must be P1, P2, P3 or P4.")

    old_priority = ticket.priority
    ticket.priority = payload.priority
    ticket.sla_hours, ticket.sla_deadline = calculate_deadline(payload.priority)

    log_activity(
        db, ticket.id, "Staff", "PRIORITY_OVERRIDDEN",
        old=old_priority, new=payload.priority, comment=payload.reason,
    )

    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/message")
def send_message(ticket_id: int, payload: StaffMessage, db: Session = Depends(get_db)):
    """Add a staff message to a ticket and detect any pending actions."""
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    pending = extract_pending_action(payload.message)
    if pending.get("pending_action"):
        ticket.pending_action = pending["pending_action"]
        ticket.pending_party = pending.get("pending_party") or "STUDENT"
        if ticket.pending_party == "STUDENT":
            ticket.status = "PENDING_STUDENT"

    log_activity(db, ticket.id, payload.actor_name, "STAFF_MESSAGE", comment=payload.message)

    db.commit()
    return {
        "message": payload.message,
        "pending_action": ticket.pending_action,
        "pending_party": ticket.pending_party,
        "status": ticket.status,
    }


@router.post("/{ticket_id}/suggest-response")
def suggest_ticket_response(ticket_id: int, db: Session = Depends(get_db)):
    """Generate an AI-suggested response for a ticket."""
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    suggested = suggest_response(
        ticket.title, ticket.description, ticket.category, ticket.status
    )
    return {"suggested_response": suggested}


@router.post("/{ticket_id}/resolve", response_model=TicketOut)
def resolve_ticket(ticket_id: int, payload: ResolveRequest, db: Session = Depends(get_db)):
    """Mark a ticket as resolved and generate a resolution summary."""
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Build conversation history for the AI summary
    activities = (
        db.query(TicketActivity)
        .filter(TicketActivity.ticket_id == ticket_id)
        .all()
    )
    conversation = "\n".join(a.comment or "" for a in activities)

    summary = payload.resolution_note or create_resolution_summary(
        ticket.title, ticket.description, conversation
    )

    old_status = ticket.status
    ticket.status = "RESOLVED"
    ticket.resolution_summary = summary
    ticket.resolved_at = datetime.utcnow()
    ticket.pending_action = None
    ticket.pending_party = None

    log_activity(
        db, ticket.id, payload.actor_name, "RESOLVED",
        old=old_status, new="RESOLVED", comment=summary,
    )

    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("/{ticket_id}/activities", response_model=list[ActivityOut])
def get_activities(ticket_id: int, db: Session = Depends(get_db)):
    """Return the full activity history for a ticket."""
    if not db.get(Ticket, ticket_id):
        raise HTTPException(status_code=404, detail="Ticket not found")

    return (
        db.query(TicketActivity)
        .filter(TicketActivity.ticket_id == ticket_id)
        .order_by(TicketActivity.created_at)
        .all()
    )
