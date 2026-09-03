# Flask + MongoDB + ChatGPT Service

A clean, modular Python & Flask REST API integrated with MongoDB and OpenAI's ChatGPT API, built with support for single-prompt execution, concurrent asynchronous batch processing, and an interactive Web UI.

> **Note for Reviewers**: As per the Case Study instructions, this project includes a built-in **dual-mode architecture**:
> - **Live OpenAI Mode**: Connects directly to OpenAI's API when an `OPENAI_API_KEY` is provided (`MOCK_OPENAI=False`).
> - **Zero-Config Mock / Demo Mode**: Enabled by default (`MOCK_OPENAI=True`) so reviewers can test all features (template substitution, MongoDB Atlas persistence, and true `asyncio.gather` parallel batch processing) immediately without requiring paid OpenAI API credits.

---

## Live Demo : https://flask-mongo-chatgpt-submission-theta.vercel.app/

## Features

- **Step 1 & 5: Single Prompt Endpoint (`POST /api/ask` or `POST /ask`)**
  - Accepts a JSON payload with `userinput`.
  - Replaces `{{userinput}}` into the prompt template fetched from MongoDB.
  - Calls OpenAI's ChatGPT API.
  - Records the request and response in MongoDB (`history` collection).
  - Returns `{"response": "..."}` in JSON format.

- **Step 2: Dynamic NoSQL Prompt Storage**
  - Prompt templates are stored in a MongoDB collection named `prompts`.
  - Automatically seeds default prompt `Education_Prompt`:
    ```json
    {
      "_id": "Education_Prompt",
      "template": "You are an expert in education domain. Answer the following: {{userinput}}"
    }
    ```

- **Step 4: Request / Response History Logging**
  - Every interaction is persisted to MongoDB in the `history` collection with timestamps and full context.

- **Step 6: Batch Asynchronous Endpoint (`POST /api/ask-batch`)**
  - Accepts a list of strings in a single request.
  - Fetches the prompt template from MongoDB.
  - Processes each string independently using asynchronous OpenAI API calls in parallel so requests do not block one another.
  - Returns the list of AI responses in the exact same order.
  - Saves all interaction pairs into the `history` collection.

- **Automated Test Suite**
  - Comprehensive unit and integration tests using `pytest` and `mongomock` (no external services needed to test).

---

## Project Structure

```
flask-mongo-chatgpt/
├── app/
│   ├── __init__.py      # Flask application factory
│   ├── config.py        # App configuration & environment variables
│   ├── db.py            # MongoDB connection & prompt seeding logic
│   ├── routes.py        # API endpoints (single & batch)
│   └── services.py      # OpenAI ChatGPT client (sync & async) & history persistence
├── tests/
│   ├── conftest.py      # Pytest fixtures with mongomock and mock OpenAI
│   └── test_api.py      # Unit & integration tests
├── .env.example         # Environment template
├── .env                 # Active configuration
├── pytest.ini           # Pytest settings
├── requirements.txt     # Python dependencies
├── run.py               # Entrypoint to run the Flask development server
├── seed_db.py           # Standalone MongoDB seeder script
└── README.md            # Documentation
```

---

## Setup & Installation

### 1. Prerequisites
- Python 3.10+
- MongoDB instance (local `mongodb://localhost:27017` or [MongoDB Atlas](https://www.mongodb.com/atlas))
- OpenAI API Key

### 2. Set Up Virtual Environment

```powershell
cd C:\Users\SHIYABUDDEN\.gemini\antigravity\scratch\flask-mongo-chatgpt
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:

```env
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=chatgpt_service

OPENAI_API_KEY=your_actual_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

FLASK_HOST=0.0.0.0
FLASK_PORT=5001
FLASK_DEBUG=True
```

### 4. (Optional) Seed Database
Run the seeder to inspect or initialize the `prompts` collection:
```powershell
python seed_db.py
```

### 5. Start the Flask Server
```powershell
python run.py
```
The server will start listening at: `http://localhost:5001`

---

## API Documentation & Examples

### 1. Single Prompt Endpoint

- **Route:** `POST /api/ask` (or `POST /ask`)
- **Headers:** `Content-Type: application/json`
- **Request Body:**
```json
{
  "userinput": "How much should I score in each subject to pass CA final?"
}
```
*Optional parameter:* `"prompt_id": "Education_Prompt"` (defaults to `"Education_Prompt"` if omitted).

- **cURL Example:**
```bash
curl -X POST http://localhost:5001/api/ask \
  -H "Content-Type: application/json" \
  -d '{"userinput": "How much should I score in each subject to pass CA final?"}'
```

- **PowerShell Example:**
```powershell
$body = @{ userinput = "How much should I score in each subject to pass CA final?" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:5001/api/ask" -Method POST -Body $body -ContentType "application/json"
```

- **Response:**
```json
{
  "response": "To pass the CA Final exam under the ICAI guidelines, you must score a minimum of 40% marks in each individual paper and a minimum of 50% aggregate marks in each group (or both groups together if appearing simultaneously)..."
}
```

---

### 2. Batch Asynchronous Endpoint

- **Route:** `POST /api/ask-batch` (or `POST /ask-batch`)
- **Headers:** `Content-Type: application/json`
- **Request Body:**
```json
{
  "userinputs": [
    "How much should I score in each subject to pass CA final?",
    "What are the subjects in CA Final Group 1?",
    "Can you explain the aggregate rule for CA exams?"
  ]
}
```

- **cURL Example:**
```bash
curl -X POST http://localhost:5001/api/ask-batch \
  -H "Content-Type: application/json" \
  -d '{
    "userinputs": [
      "How much should I score in each subject to pass CA final?",
      "What are the subjects in CA Final Group 1?",
      "Can you explain the aggregate rule for CA exams?"
    ]
  }'
```

- **PowerShell Example:**
```powershell
$body = @{
    userinputs = @(
        "How much should I score in each subject to pass CA final?",
        "What are the subjects in CA Final Group 1?",
        "Can you explain the aggregate rule for CA exams?"
    )
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5001/api/ask-batch" -Method POST -Body $body -ContentType "application/json"
```

- **Response:**
```json
{
  "responses": [
    "To pass the CA Final exam, you must score at least 40% in each individual paper and...",
    "Under the new ICAI syllabus, CA Final Group 1 comprises: Paper 1: Financial Reporting...",
    "The aggregate rule requires you to score at least 50% total marks across all papers in the group..."
  ]
}
```

---

### 3. Inspect History & Prompts

- **List Prompts:** `GET /api/prompts`
- **View History:** `GET /api/history?limit=10`
- **Health Check:** `GET /api/health`

---

## Running the Automated Tests

Run the test suite using `pytest`:
```powershell
.\.venv\Scripts\pytest -v
```

All 8 tests execute in memory using `mongomock` and mock OpenAI clients, verifying prompt substitution, API response structures, MongoDB history persistence, and asynchronous concurrency.
