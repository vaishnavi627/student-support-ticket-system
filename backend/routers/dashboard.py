from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Ticket

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    """Return a summary of ticket counts by status and priority."""
    tickets = db.query(Ticket).all()
    now = datetime.utcnow()

    return {
        "total": len(tickets),
        "open": sum(t.status not in {"RESOLVED", "CLOSED"} for t in tickets),
        "resolved": sum(t.status == "RESOLVED" for t in tickets),
        "overdue": sum(
            t.status not in {"RESOLVED", "CLOSED"}
            and t.sla_deadline is not None
            and t.sla_deadline < now
            for t in tickets
        ),
        "escalated": sum(t.status == "ESCALATED" for t in tickets),
        "p1": sum(t.priority == "P1" for t in tickets),
        "p2": sum(t.priority == "P2" for t in tickets),
        "p3": sum(t.priority == "P3" for t in tickets),
        "p4": sum(t.priority == "P4" for t in tickets),
    }
