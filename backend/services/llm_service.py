import json, logging, os, re

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)

def _completion(messages, temperature):
    key = os.getenv("OPENAI_API_KEY")
    if not key or OpenAI is None:
        return None
    try:
        client = OpenAI(
            api_key=key,
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=temperature,
            messages=messages,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        logger.warning("OpenAI request failed; using deterministic fallback: %s", exc)
        return None

def demo_analyze(title, description):
    text = f"{title} {description}".lower()
    if any(k in text for k in ["exam tomorrow", "hall ticket", "exam today", "examination tomorrow"]):
        p, dept, reason = "P1", "Examination", "The request may affect access to an imminent examination."
        cat = "Examination"
    elif any(k in text for k in ["fee", "payment", "fees"]):
        p, dept, reason = "P2", "Accounts", "The request relates to a fee or payment issue."
        cat = "Fees"
    elif any(k in text for k in ["certificate", "transfer certificate", "bonafide"]):
        p, dept, reason = "P3", "Administration", "The request relates to an administrative document."
        cat = "Certificate"
    elif any(k in text for k in ["attendance", "absent", "attendance mark"]):
        p, dept, reason = "P3", "Academic", "The request relates to an attendance record."
        cat = "Attendance"
    else:
        p, dept, reason = "P4", "Student Services", "No immediate critical impact was identified."
        cat = "Other"
    return {"category": cat, "summary": description[:240], "priority": p,
            "department": dept, "reason": reason, "confidence": 0.72}

def _json(text):
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m: raise ValueError("LLM did not return JSON")
    return json.loads(m.group(0))

def analyze_ticket(title, description):
    prompt = f'''Return JSON only:
{{"category":"Fees|Attendance|ID Card|Certificate|Documents|Examination|Hostel|Other",
"summary":"short factual summary","priority":"P1|P2|P3|P4",
"department":"Accounts|Academic|Administration|Examination|Student Services|Hostel",
"reason":"short reason","confidence":0.0}}
Do not invent deadlines. P1 means potentially critical/time-sensitive impact.
Title: {title}
Description: {description}'''
    content = _completion(
        [{"role":"system","content":"Return valid JSON only."},
         {"role":"user","content":prompt}],
        temperature=0,
    )
    if content is None:
        return demo_analyze(title, description)
    try:
        result = _json(content)
    except (ValueError, json.JSONDecodeError):
        return demo_analyze(title, description)
    if result.get("priority") not in {"P1","P2","P3","P4"}:
        result["priority"] = "P3"
    return result

def suggest_response(title, description, category, status):
    content = _completion(
        [{"role":"system","content":"Draft concise professional support replies. Do not promise unknown outcomes."},
         {"role":"user","content":f"Title: {title}\nDescription: {description}\nCategory: {category}\nStatus: {status}"}],
        temperature=0.2,
    )
    return content or f"Dear Student,\n\nWe received your request regarding '{title}'. Our {category} team is reviewing it. We will contact you if more information is required.\n\nRegards,\nStudent Support Team"

def extract_pending_action(message):
    content = _completion(
        [{"role":"system","content":"Return JSON only with pending_action and pending_party."},
         {"role":"user","content":f"Analyze this staff message. pending_party must be STUDENT, STAFF, DEPARTMENT or empty.\n{message}"}],
        temperature=0,
    )
    if content is None:
        if any(k in message.lower() for k in ["upload","submit","provide","send"]):
            return {"pending_action": message, "pending_party": "STUDENT"}
        return {"pending_action": "", "pending_party": ""}
    try:
        return _json(content)
    except (ValueError, json.JSONDecodeError):
        return {"pending_action": "", "pending_party": ""}

def create_resolution_summary(title, description, conversation):
    content = _completion(
        [{"role":"system","content":"Create a short factual resolution summary. Never invent outcomes."},
         {"role":"user","content":f"Title: {title}\nRequest: {description}\nConversation:\n{conversation}"}],
        temperature=0.2,
    )
    return content or f"Resolved request: {title}. Staff reviewed the ticket and recorded the resolution."
