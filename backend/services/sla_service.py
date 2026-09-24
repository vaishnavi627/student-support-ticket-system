from datetime import datetime, timedelta

SLA_HOURS = {"P1": 4, "P2": 24, "P3": 72, "P4": 120}

def get_sla_hours(priority):
    return SLA_HOURS.get(priority, 72)

def calculate_deadline(priority, start=None):
    start = start or datetime.utcnow()
    hours = get_sla_hours(priority)
    return hours, start + timedelta(hours=hours)
