# AI-Powered Student Support & Ticket Management

FastAPI backend + Streamlit/CSS frontend for AI-powered student support ticket management.

Workflow:
Student creates ticket -> LLM analyzes category/summary/priority/department -> deterministic SLA engine -> staff dashboard -> staff conversation -> LLM suggested response/pending action/resolution summary.

If OPENAI_API_KEY is not configured, the app uses a deterministic demo classifier so the complete workflow can still be demonstrated.

## Clone and run locally

### 1. Clone the repository

```powershell
git clone https://github.com/vaishnavi627/student-support-ticket-system.git
cd student-support-ticket-system
```

### 2. Create the Python environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

If PowerShell blocks activation, run this once in the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

### 3. Configure environment variables

Create a file named `.env` in the project root. Never commit this file or share its API key.

```env
OPENAI_API_KEY=your_groq_or_openai_api_key_here
OPENAI_MODEL=llama-3.1-8b-instant
OPENAI_BASE_URL=https://api.groq.com/openai/v1
API_BASE_URL=http://127.0.0.1:8000
```

The application also works without `OPENAI_API_KEY` by using its deterministic demo classifier.

### 4. Start the backend

Open a terminal in the project folder, activate the environment, and run:

```powershell
.venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload
```

Leave this terminal running. FastAPI documentation is available at <http://127.0.0.1:8000/docs>.

### 5. Start the frontend

Open a second terminal in the project folder and run:

```powershell
.venv\Scripts\Activate.ps1
streamlit run frontend/app.py
```

Open the URL shown by Streamlit, normally <http://localhost:8501>.

## Run with Docker

Make sure Docker Desktop is running, then execute:

```powershell
docker compose up --build
```

Open the frontend at <http://localhost:8501> and the API docs at <http://localhost:8000/docs>.
Stop the containers with:

```powershell
docker compose down
```

## Production improvements
Use PostgreSQL, JWT/OAuth, S3, background workers for SLA monitoring, role-based authorization, tests and CI/CD.
