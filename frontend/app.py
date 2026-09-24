import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

from frontend.api import (
    assign_ticket,
    create_ticket,
    dashboard_summary,
    get_activities,
    get_ticket,
    get_tickets,
    override_priority,
    resolve_ticket,
    send_staff_message,
    suggest_response,
    update_status,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Student Support Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

css = Path(__file__).parent / "styles.css"
st.markdown(f"<style>{css.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-logo">
            <span class="logo-icon">🎓</span>
            <div class="logo-text">Student Support</div>
            <div class="logo-sub">Ticket Management System</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    role = st.selectbox(
        "**Select your role**",
        ["Student", "Staff", "Manager"],
        help="Choose your role to access the appropriate view.",
    )
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<div style='color:#484f58;font-size:0.75rem;text-align:center;'>Powered by AI · FastAPI · Streamlit</div>",
        unsafe_allow_html=True,
    )

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">AI Student Support Portal</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">AI-powered classification · SLA management · Staff workflow</div>',
    unsafe_allow_html=True,
)

# ── Backend connectivity check ────────────────────────────────────────────────
try:
    summary = dashboard_summary()
except Exception:
    st.error(
        "⚠️  Backend is not running.  \n"
        "Start it with: `uvicorn backend.main:app --reload`"
    )
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# STUDENT ROLE
# ═══════════════════════════════════════════════════════════════════════════════
if role == "Student":

    # ── Create ticket form ────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-header"><div class="icon">✦</div><div class="label">Submit a Support Ticket</div></div>',
        unsafe_allow_html=True,
    )

    with st.form("create_ticket_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", placeholder="e.g. Gowtham A S")
        with col2:
            email = st.text_input("Email Address", placeholder="e.g. student@college.edu")

        title = st.text_input("Subject", placeholder="Brief description of your issue")
        desc = st.text_area(
            "Describe Your Issue",
            placeholder="Provide as much detail as possible so we can help you faster...",
            height=160,
        )
        submit = st.form_submit_button("🚀  Submit Ticket", type="primary", use_container_width=True)

    if submit:
        if not name.strip():
            st.warning("⚠️  Please enter your full name.")
        elif not email.strip() or "@" not in email:
            st.warning("⚠️  Please enter a valid email address.")
        elif not title.strip():
            st.warning("⚠️  Please enter a subject for your ticket.")
        elif not desc.strip():
            st.warning("⚠️  Please describe your issue.")
        else:
            with st.spinner("Analyzing your ticket with AI..."):
                try:
                    t = create_ticket({
                        "student_name": name,
                        "student_email": email,
                        "title": title,
                        "description": desc,
                    })
                    st.success(f"✅  Ticket **{t['ticket_number']}** created successfully!")
                    st.markdown(
                        f"""
                        <div class="ai-box">
                            <b>AI Classification Result</b><br><br>
                            <b>Ticket:</b> {t['ticket_number']}<br>
                            <b>Category:</b> {t['category']}<br>
                            <b>Priority:</b> {t['priority']}<br>
                            <b>Department:</b> {t['department']}<br>
                            <b>SLA Deadline:</b> {t['sla_deadline']}<br><br>
                            <b>Summary:</b> {t['ai_summary']}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                except Exception as e:
                    st.error(f"Failed to create ticket: {e}")

    # ── Ticket list ───────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div class="section-header"><div class="icon">📋</div><div class="label">All Tickets</div></div>',
        unsafe_allow_html=True,
    )

    tickets = get_tickets()
    if not tickets:
        st.markdown(
            '<div class="info-banner">No tickets found. Submit your first ticket above.</div>',
            unsafe_allow_html=True,
        )
    else:
        for t in tickets:
            priority = t["priority"].lower()
            status = t["status"]
            st.markdown(
                f"""
                <div class="ticket-card {priority}">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                        <div>
                            <span style="font-size:0.8rem; color:#8b949e; letter-spacing:0.05em; text-transform:uppercase;">
                                {t['ticket_number']}
                            </span><br>
                            <span style="font-size:1rem; font-weight:700; color:#f0f6fc;">{t['title']}</span>
                        </div>
                        <div style="display:flex; gap:8px; align-items:center;">
                            <span class="badge badge-{priority}">{t['priority']}</span>
                            <span class="badge-status">{status}</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════════════════════════
# STAFF / MANAGER ROLE
# ═══════════════════════════════════════════════════════════════════════════════
else:
    heading = "Management Overview" if role == "Manager" else "Staff Dashboard"
    st.markdown(
        f'<div class="section-header"><div class="icon">📊</div><div class="label">{heading}</div></div>',
        unsafe_allow_html=True,
    )

    # ── Dashboard metrics ─────────────────────────────────────────────────────
    cols = st.columns(6)
    metrics = [
        ("Total", summary["total"]),
        ("Open", summary["open"]),
        ("Resolved", summary["resolved"]),
        ("Overdue", summary["overdue"]),
        ("Escalated", summary["escalated"]),
        ("P1 Critical", summary["p1"]),
    ]
    for col, (label, val) in zip(cols, metrics):
        col.metric(label, val)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Ticket selector ───────────────────────────────────────────────────────
    tickets = get_tickets()
    if not tickets:
        st.markdown(
            '<div class="info-banner">No tickets yet. Create one using the Student role.</div>',
            unsafe_allow_html=True,
        )
        st.stop()

    options = {f"{t['ticket_number']}  —  {t['title']}": t["id"] for t in tickets}
    selected = st.selectbox("🔍  Select a Ticket", list(options))
    tid = options[selected]
    t = get_ticket(tid)

    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns([2, 1], gap="large")

    # ── LEFT: Ticket detail + AI analysis ────────────────────────────────────
    with col_left:
        priority = t["priority"].lower()
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:12px; margin-bottom:0.5rem;">
                <span style="font-size:1.4rem; font-weight:800; color:#f0f6fc;">{t['ticket_number']}</span>
                <span class="badge badge-{priority}">{t['priority']}</span>
                <span class="badge-status">{t['status']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='color:#8b949e; line-height:1.7;'>{t['description']}</p>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="ai-box">
                <b>AI Analysis</b><br><br>
                <b>Category:</b> {t['category']}<br>
                <b>Priority:</b> {t['priority']}<br>
                <b>Department:</b> {t['department']}<br>
                <b>Confidence:</b> {t['ai_confidence']}<br><br>
                <b>Summary:</b> {t['ai_summary']}<br><br>
                <b>Reason:</b> {t['ai_reason']}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if t["pending_action"]:
            st.markdown(
                f"""
                <div class="pending-box">
                    <b>⏳ Pending Action</b><br>
                    {t['pending_action']}<br>
                    <small>Awaiting: <b>{t['pending_party']}</b></small>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── RIGHT: Actions panel ──────────────────────────────────────────────────
    with col_right:

        # SLA info
        st.markdown(
            f"""
            <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08);
                        border-radius:14px; padding:1rem 1.2rem; margin-bottom:1rem;">
                <div style="color:#8b949e; font-size:0.72rem; font-weight:600; letter-spacing:0.07em;
                             text-transform:uppercase; margin-bottom:0.4rem;">SLA Information</div>
                <div style="font-size:1.6rem; font-weight:800; background:linear-gradient(135deg,#6366f1,#06b6d4);
                             -webkit-background-clip:text; -webkit-text-fill-color:transparent;">{t['sla_hours']}h</div>
                <div style="color:#8b949e; font-size:0.8rem; margin-top:4px;">Deadline: {t['sla_deadline']}</div>
                <div style="color:#8b949e; font-size:0.8rem;">Status: <b style="color:#f0f6fc;">{t['status']}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Assign
        st.markdown(
            '<div class="section-header"><div class="icon">👤</div><div class="label">Assign Ticket</div></div>',
            unsafe_allow_html=True,
        )
        with st.form("assign_form"):
            sn = st.text_input("Staff Name", placeholder="e.g. Accounts Staff")
            se = st.text_input("Staff Email", placeholder="e.g. staff@college.edu")
            dep = st.text_input("Department", value=t["department"])
            if st.form_submit_button("Assign →", use_container_width=True):
                if not sn.strip() or not se.strip():
                    st.warning("Staff name and email are required.")
                else:
                    assign_ticket(tid, {"staff_name": sn, "staff_email": se, "department": dep})
                    st.success("Ticket assigned successfully.")
                    st.rerun()

        # Status update
        st.markdown(
            '<div class="section-header"><div class="icon">🔄</div><div class="label">Update Status</div></div>',
            unsafe_allow_html=True,
        )
        ns = st.selectbox(
            "New Status",
            ["ASSIGNED", "IN_PROGRESS", "PENDING_STUDENT", "PENDING_DEPARTMENT", "ESCALATED", "CLOSED"],
        )
        if st.button("Update Status →", use_container_width=True):
            update_status(tid, {"status": ns, "comment": "Updated from dashboard"})
            st.success("Status updated.")
            st.rerun()

        # Priority override
        st.markdown(
            '<div class="section-header"><div class="icon">⚡</div><div class="label">Priority Override</div></div>',
            unsafe_allow_html=True,
        )
        p = st.selectbox(
            "Priority",
            ["P1", "P2", "P3", "P4"],
            index=["P1", "P2", "P3", "P4"].index(t["priority"]),
        )
        reason = st.text_input("Reason for Override", placeholder="Explain why you're changing the priority")
        if st.button("Override Priority →", use_container_width=True):
            if not reason.strip():
                st.warning("A reason is required to override priority.")
            else:
                override_priority(tid, {"priority": p, "reason": reason})
                st.success("Priority updated.")
                st.rerun()

    # ── Staff Conversation ────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div class="section-header"><div class="icon">💬</div><div class="label">Staff Conversation</div></div>',
        unsafe_allow_html=True,
    )

    staff_actor = st.text_input("Your Name (Staff)", placeholder="Enter your name", key="actor_name")

    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        if st.button("✦ Generate AI Response", use_container_width=True):
            with st.spinner("Generating AI response..."):
                st.session_state["suggested"] = suggest_response(tid)["suggested_response"]

    msg = st.text_area(
        "Message",
        value=st.session_state.get("suggested", ""),
        placeholder="Type your message to the student...",
        height=130,
    )

    col_send, col_resolve = st.columns(2)
    with col_send:
        if st.button("📨  Send Message", use_container_width=True):
            if not staff_actor.strip():
                st.warning("Please enter your staff name.")
            elif not msg.strip():
                st.warning("Message cannot be empty.")
            else:
                r = send_staff_message(tid, {"actor_name": staff_actor, "message": msg})
                st.success("Message sent.")
                if r.get("pending_action"):
                    st.info(f"⏳ Pending action detected: {r['pending_action']}")
                st.rerun()

    with col_resolve:
        note = st.text_area("Resolution Note (optional)", placeholder="Summarise the resolution...", height=70)
        if st.button("✅  Resolve Ticket", type="primary", use_container_width=True):
            if not staff_actor.strip():
                st.warning("Please enter your staff name.")
            else:
                with st.spinner("Generating resolution summary..."):
                    r = resolve_ticket(tid, {"actor_name": staff_actor, "resolution_note": note or None})
                st.success("Ticket resolved.")
                st.markdown(
                    f"<div class='ai-box'><b>Resolution Summary</b><br><br>{r['resolution_summary']}</div>",
                    unsafe_allow_html=True,
                )
                st.rerun()

    # ── Activity History ──────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div class="section-header"><div class="icon">📜</div><div class="label">Activity History</div></div>',
        unsafe_allow_html=True,
    )

    activities = get_activities(tid)
    if not activities:
        st.markdown(
            '<div class="info-banner">No activity recorded yet for this ticket.</div>',
            unsafe_allow_html=True,
        )
    else:
        for x in activities:
            comment_html = (
                f"<div class='activity-comment'>{x['comment']}</div>"
                if x["comment"]
                else ""
            )
            st.markdown(
                f"""
                <div class="activity-item">
                    <div class="activity-dot"></div>
                    <div class="activity-content">
                        <div class="activity-action">{x['action']}</div>
                        <div class="activity-meta">by {x['actor_name']} · {x['created_at']}</div>
                        {comment_html}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
