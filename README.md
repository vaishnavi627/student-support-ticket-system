# AI-Powered Student Support & Ticket Management

FastAPI backend + Streamlit/CSS frontend for AI-powered student support ticket management.

Workflow:
Student creates ticket -> LLM analyzes category/summary/priority/department -> deterministic SLA engine -> staff dashboard -> staff conversation -> LLM suggested response/pending action/resolution summary.

If OPENAI_API_KEY is not configured, the app uses a deterministic demo classifier so the complete workflow can still be demonstrated.

## Run

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

Edit `.env` and fill in your API key.

The app supports OpenAI-compatible providers such as Groq. For Groq, set these values in `.env`:

```env
OPENAI_API_KEY=your_groq_or_openai_api_key_here
OPENAI_MODEL=llama-3.1-8b-instant
OPENAI_BASE_URL=https://api.groq.com/openai/v1
```

Terminal 1:
```powershell
uvicorn backend.main:app --reload
```

Terminal 2:
```powershell
streamlit run frontend/app.py
```

FastAPI docs: http://127.0.0.1:8000/docs
Streamlit: http://localhost:8501

## Production improvements
Use PostgreSQL, JWT/OAuth, S3, background workers for SLA monitoring, role-based authorization, tests and CI/CD.
