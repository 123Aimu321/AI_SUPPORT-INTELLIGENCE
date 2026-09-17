Absolutely. Below is a **complete, professional README.md** for your `ai-support-intelligence` repository, covering the assessment requirements, architecture, setup, API usage, UI, LLM integration, anomaly logic, testing, troubleshooting, and walkthrough points.

# AI Support Intelligence

An AI-powered customer support intelligence system built for the **DOTMappers IT Pvt. Ltd. AI Engineer Technical Assessment**.

The system ingests customer support tickets from a CSV file, stores them in SQLite, understands natural-language questions using an LLM, converts them into structured query intents, executes safe database queries, detects support-ticket anomalies, and exposes the functionality through a FastAPI REST API and Streamlit web interface.

---

## 📌 Project Overview

Customer support teams often have large amounts of ticket data but need a simple way to ask questions such as:

* How many tickets are currently open?
* Which agent resolved the most tickets this month?
* Show me all Critical tickets not resolved within 12 hours.
* What is the average customer rating for Technical category tickets?
* Are there any anomalies in resolution times this week?

This project provides an AI-powered interface for answering these questions without requiring the user to write SQL.

### Core Workflow

```text
                 support_tickets.csv
                         │
                         ▼
                  Data Ingestion
                         │
                         ▼
                  SQLite Database
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
        Natural Language       Anomaly Engine
             Query                    │
              │                       │
              ▼                       ▼
          Groq LLM              Deterministic
       Intent Detection        Anomaly Detection
              │                       │
              ▼                       │
       Intent Validation              │
              │                       │
              ▼                       │
         Safe SQL Query               │
              │                       │
              └──────────┬────────────┘
                         ▼
                    FastAPI REST API
                         │
                         ▼
                   Streamlit UI
```

---

# ✨ Features

## 1. CSV Data Ingestion

The application automatically loads the provided `support_tickets.csv` dataset into SQLite.

The ingestion layer:

* Validates required columns
* Parses date fields
* Converts numerical fields
* Removes unnecessary whitespace
* Validates ticket IDs
* Detects duplicate ticket IDs
* Detects missing required identifiers
* Creates/refreshes the SQLite database

---

## 2. Natural-Language Querying

Users can ask questions using normal English instead of SQL.

Example:

```text
How many tickets are currently open?
```

The LLM converts the question into a structured intent such as:

```json
{
  "intent": "count",
  "filters": [
    {
      "column": "status",
      "operator": "=",
      "value": "Open"
    }
  ],
  "aggregation": null,
  "group_by": null,
  "order": "desc",
  "limit": 100,
  "time_period": null
}
```

The application then validates the intent and generates the SQL query itself.

The LLM does **not** directly execute arbitrary SQL.

---

## 3. AI-Powered Query Understanding

The system uses the Groq API with the configured LLM model to understand natural-language questions.

The current default model is:

```text
openai/gpt-oss-20b
```

The LLM is used for:

* Understanding user questions
* Identifying the required operation
* Identifying filters
* Identifying grouping
* Identifying sorting
* Identifying time periods
* Generating a concise natural-language explanation of results

---

## 4. Safe Query Execution

Instead of allowing the LLM to generate unrestricted SQL, the application follows:

```text
User Question
      ↓
LLM
      ↓
Structured Intent
      ↓
Validation
      ↓
Application-generated SQL
      ↓
SQLite
```

This provides better control over:

* Allowed columns
* Allowed operators
* Allowed aggregations
* Allowed grouping fields
* Result limits
* Time periods
* Query structure

SQL values are parameterized rather than directly concatenated into SQL statements.

---

# 🚨 5. Anomaly Detection

Anomaly detection is implemented separately from the LLM.

This is intentional.

The LLM is responsible for natural-language understanding, while deterministic Python logic handles anomaly detection so that the rules remain predictable and reproducible.

The system detects cases including:

### Critical unresolved tickets

Critical-priority tickets that remain unresolved beyond the configured threshold.

### High-priority unresolved tickets

High-priority tickets that remain unresolved beyond the configured threshold.

### Long unresolved tickets

Unresolved tickets that have remained open for an extended period.

### Resolution-time outliers

Unusually high resolution times detected using an IQR-based statistical method.

### Response-time outliers

Unusually high response times detected using an IQR-based statistical method.

Statistical outliers are reported separately from active SLA-style issues.

---

# 🌐 REST API

The application exposes its functionality using **FastAPI REST APIs**.

## API Endpoints

| Method | Endpoint                       | Description                                   |
| ------ | ------------------------------ | --------------------------------------------- |
| GET    | `/health`                      | Check API health                              |
| POST   | `/query`                       | Ask a natural-language question               |
| GET    | `/anomalies`                   | Detect anomalies                              |
| GET    | `/anomalies?period=this_week`  | Detect anomalies for the latest dataset week  |
| GET    | `/anomalies?period=this_month` | Detect anomalies for the latest dataset month |

---

# 🔍 Query API

## Endpoint

```http
POST /query
```

### Request

```json
{
  "question": "How many tickets are currently open?"
}
```

### Example Response

```json
{
  "question": "How many tickets are currently open?",
  "answer": "There are 123 open tickets.",
  "result": [
    {
      "count": 123
    }
  ],
  "intent": {
    "intent": "count",
    "filters": [
      {
        "column": "status",
        "operator": "=",
        "value": "Open"
      }
    ]
  }
}
```

The exact result values depend on the dataset.

---

# 🚨 Anomaly API

## All Tickets

```http
GET /anomalies
```

## This Week

```http
GET /anomalies?period=this_week
```

## This Month

```http
GET /anomalies?period=this_month
```

The response contains detected anomalies along with information such as:

* Ticket ID
* Priority
* Status
* Category
* Agent
* Resolution time
* Response time
* Anomaly type
* Reason

---

# ❤️ Health API

## Endpoint

```http
GET /health
```

Example response:

```json
{
  "status": "healthy",
  "service": "AI Support Intelligence"
}
```

---

# 🖥️ Streamlit UI

A minimal Streamlit interface is included.

The UI provides two primary sections:

### 💬 Ask Questions

Users can enter questions such as:

```text
How many tickets are currently open?
```

```text
Which agent resolved the most tickets this month?
```

```text
What is the average customer rating for Technical category tickets?
```

The UI sends the question to the FastAPI `/query` endpoint.

---

### 🚨 Anomalies

The anomaly section allows users to select:

```text
All tickets
This week
This month
```

The UI displays:

* Total anomalies
* Critical anomalies
* High anomalies
* Medium anomalies
* Individual anomaly details

---

# 📁 Project Structure

```text
ai-support-intelligence/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes_query.py
│   │   ├── routes_anomaly.py
│   │   └── routes_health.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── database.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm_service.py
│   │   ├── query_service.py
│   │   ├── anomaly_service.py
│   │   └── ingestion.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py
│   │
│   └── utils/
│       ├── __init__.py
│       └── sql_validator.py
│
├── data/
│   └── support_tickets.csv
│
├── database/
│   └── support_tickets.db
│
├── ui/
│   └── streamlit_app.py
│
├── tests/
│   ├── test_api.py
│   ├── test_anomaly.py
│   └── test_query.py
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

# 🛠️ Technology Stack

| Component            | Technology           |
| -------------------- | -------------------- |
| Programming Language | Python               |
| API Framework        | FastAPI              |
| Web UI               | Streamlit            |
| Database             | SQLite               |
| Data Processing      | Pandas               |
| Numerical Processing | NumPy                |
| ORM / Database Layer | SQLAlchemy           |
| LLM                  | Groq API             |
| LLM Model            | `openai/gpt-oss-20b` |
| API Server           | Uvicorn              |
| Testing              | Pytest               |

---

# 📊 Dataset

The application uses:

```text
data/support_tickets.csv
```

The dataset contains 500 support tickets.

## Columns

| Column                | Description                    |
| --------------------- | ------------------------------ |
| `ticket_id`           | Unique ticket identifier       |
| `created_at`          | Ticket creation timestamp      |
| `category`            | Billing, Technical, or General |
| `priority`            | Low, Medium, High, or Critical |
| `status`              | Open, Resolved, or Escalated   |
| `response_time_hrs`   | Time taken to respond          |
| `resolution_time_hrs` | Time taken to resolve          |
| `agent_id`            | Support agent identifier       |
| `customer_rating`     | Customer rating                |
| `issue_summary`       | Short description of the issue |

For unresolved tickets, resolution time and customer rating may be unavailable.

---

# ⚙️ Installation

## Requirements

Install:

* Python 3.10+
* Git
* A Groq API key

No paid database or cloud infrastructure is required.

---

# 1. Clone the Repository

After the project is uploaded to GitHub:

```powershell
git clone https://github.com/123Aimu321/ai-support-intelligence.git
```

Enter the project directory:

```powershell
cd ai-support-intelligence
```

---

# 2. Create a Virtual Environment

Windows PowerShell:

```powershell
py -3.13 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

# 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

---

# 4. Configure the Groq API

Create a file named:

```text
.env
```

Add:

```env
GROQ_API_KEY=your_actual_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
```

Never commit the real `.env` file to GitHub.

The repository should contain `.env.example`, not the actual API key.

---

# 5. Load the Dataset

The database is initialized automatically when the FastAPI application starts.

You can also manually initialize it using:

```powershell
python -c "from app.services.ingestion import initialize_database; print('Loaded tickets:', initialize_database())"
```

Expected output:

```text
Loaded tickets: 500
```

This creates:

```text
database/support_tickets.db
```

---

# ▶️ Running the Application

## Start the FastAPI Server

From the project root:

```powershell
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

FastAPI also provides interactive API documentation at:

```text
http://127.0.0.1:8000/docs
```

---

# ▶️ Start the Streamlit UI

Open a second PowerShell terminal.

Navigate to the project:

```powershell
cd "C:\Users\aiman\Desktop\new\ai intern\ai-support-intelligence"
```

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Run:

```powershell
streamlit run ui/streamlit_app.py
```

The UI will normally open at:

```text
http://localhost:8501
```

---

# 🧪 Testing the API

Once FastAPI is running, open:

```text
http://127.0.0.1:8000/docs
```

The Swagger interface allows the evaluator to test:

```text
GET /health
POST /query
GET /anomalies
```

---

# 💬 Example Natural-Language Questions

The following questions are supported:

### Ticket Count

```text
How many tickets are currently open?
```

### Agent Performance

```text
Which agent resolved the most tickets this month?
```

### Critical Tickets

```text
Show me all Critical tickets not resolved within 12 hours.
```

### Customer Rating

```text
What is the average customer rating for Technical category tickets?
```

### Anomalies

```text
Are there any anomalies in resolution times this week?
```

Other supported questions can include:

```text
How many tickets are in the Billing category?
```

```text
How many High priority tickets are there?
```

```text
What is the average response time?
```

```text
What is the average resolution time for Technical tickets?
```

```text
Show me unresolved Critical tickets.
```

---

# 🧠 LLM Architecture

The LLM is not used to directly access the database.

Instead, it acts as a natural-language understanding layer.

### Step 1 — User asks a question

```text
How many open tickets are there?
```

### Step 2 — LLM identifies intent

```json
{
  "intent": "count",
  "filters": [
    {
      "column": "status",
      "operator": "=",
      "value": "Open"
    }
  ]
}
```

### Step 3 — Application validates the intent

The validator checks:

* Intent
* Columns
* Operators
* Aggregations
* Grouping
* Sorting
* Result limits
* Time period

### Step 4 — Application generates SQL

The SQL is created by Python rather than trusting arbitrary LLM-generated SQL.

### Step 5 — SQLite executes the query

```text
SQLite
   ↓
Query Result
```

### Step 6 — LLM explains the result

The result is passed back to the LLM to generate a concise natural-language response.

---

# 🔐 Security and Query Safety

Several controls are implemented to prevent unrestricted database access.

## Allowed Columns

Only predefined dataset columns can be queried.

## Allowed Operations

Only supported operations are accepted:

```text
count
average
sum
minimum
maximum
group_count
group_average
list
```

## Parameterized Values

Database values are passed using SQL parameters rather than unsafe string concatenation.

## Result Limits

The query layer limits returned records to prevent unnecessarily large responses.

## No Arbitrary SQL From the LLM

The LLM generates a structured intent, not executable SQL.

The application validates the intent and constructs the SQL.

---

# 🚨 Anomaly Detection Design

Anomaly detection is deliberately deterministic.

This avoids relying on an LLM for numerical or rule-based decisions.

## Rule-Based Detection

Examples:

```text
Critical + unresolved + older than threshold
```

```text
High + unresolved + older than threshold
```

```text
Unresolved + older than extended threshold
```

## Statistical Detection

For response and resolution times, the application uses the Interquartile Range (IQR) approach.

Conceptually:

```text
IQR = Q3 - Q1

Lower Bound = Q1 - 1.5 × IQR
Upper Bound = Q3 + 1.5 × IQR
```

Values outside the expected range can be flagged as statistical outliers.

This provides a simple and explainable anomaly-detection approach suitable for the assessment dataset.

---

# 📅 Time Period Handling

The system supports:

```text
this_week
this_month
```

Because the assessment dataset is historical rather than a continuously updated production stream, the application uses the latest available dataset timestamp as the reference point for these relative periods.

This makes the behavior deterministic when the application is evaluated later.

---

# 🧪 Test Suite

Tests are located in:

```text
tests/
```

including:

```text
test_api.py
test_anomaly.py
test_query.py
```

Run:

```powershell
pytest
```

The tests cover key application behavior such as:

* API responses
* Query processing
* Anomaly detection
* Validation

---

# 🐛 Common Problems

## Groq API Error

If the application reports an authentication error:

Check:

```text
.env
```

Make sure:

```env
GROQ_API_KEY=your_actual_key
```

is present.

---

## Model Error

Check:

```env
GROQ_MODEL=openai/gpt-oss-20b
```

The model must be available for the configured Groq account.

---

## Database Not Found

Run:

```powershell
python -c "from app.services.ingestion import initialize_database; print('Loaded tickets:', initialize_database())"
```

The database will be recreated from the CSV.

---

## API Connection Error in Streamlit

Make sure FastAPI is running first:

```powershell
uvicorn app.main:app --reload
```

Then start Streamlit:

```powershell
streamlit run ui/streamlit_app.py
```

The Streamlit UI expects the API at:

```text
http://127.0.0.1:8000
```

---

# 🔄 Complete Startup Flow

For a fresh machine:

```text
1. Install Python
        ↓
2. Clone GitHub repository
        ↓
3. Open project folder
        ↓
4. Create virtual environment
        ↓
5. Activate virtual environment
        ↓
6. pip install -r requirements.txt
        ↓
7. Create .env
        ↓
8. Add Groq API key
        ↓
9. Start FastAPI
        ↓
10. Start Streamlit
        ↓
11. Open browser
        ↓
12. Ask questions / check anomalies
```

---

# 🖥️ Evaluator Quick Start

After cloning the repository:

```powershell
cd ai-support-intelligence
```

Create and activate the environment:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Configure `.env`:

```env
GROQ_API_KEY=your_actual_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
```

Start the API:

```powershell
uvicorn app.main:app --reload
```

In another terminal:

```powershell
streamlit run ui/streamlit_app.py
```

Then open:

```text
http://localhost:8501
```

For API testing:

```text
http://127.0.0.1:8000/docs
```

---

# 🏗️ Design Decisions

## Why SQLite?

SQLite was selected because:

* No external database server is required
* No Docker database setup is required
* It is completely free
* It is sufficient for the 500-row assessment dataset
* It makes evaluator setup simple

For production workloads, PostgreSQL or another managed database could be introduced.

---

## Why FastAPI?

FastAPI provides:

* REST API support
* Automatic request validation
* Type-safe schemas
* Swagger/OpenAPI documentation
* High performance
* Simple Python integration

---

## Why Streamlit?

Streamlit was selected for the minimal UI because it allows the project to provide a usable interface without introducing unnecessary frontend complexity.

The UI communicates with the FastAPI backend rather than directly accessing the database.

---

## Why Deterministic Anomaly Detection?

Anomaly detection involves numerical and rule-based decisions.

Using deterministic Python logic makes the results:

* Reproducible
* Explainable
* Testable
* Independent of LLM randomness

The LLM is therefore used where it provides the most value: natural-language understanding and result explanation.

---

# ⚖️ Trade-offs

### SQLite vs PostgreSQL

SQLite reduces setup complexity but is not ideal for a large multi-user production system.

### Streamlit vs React

Streamlit allows rapid development of a minimal assessment UI. React would provide greater control for a production frontend.

### Groq vs Local LLM

Groq provides a simple hosted inference option with a free tier, while a local Ollama model could remove the external API dependency but would require local model resources.

### Structured Intent vs LLM-Generated SQL

Structured intent requires more application-side logic but provides significantly better control and safety than executing arbitrary LLM-generated SQL.

---

# 🚀 Possible Future Improvements

For a production-ready version, the system could be extended with:

* PostgreSQL
* Authentication and authorization
* Role-based access control
* Background ingestion jobs
* Scheduled anomaly detection
* Email/Slack alerts
* Agent performance dashboards
* More advanced SLA rules
* Configurable anomaly thresholds
* Caching
* Query history
* Conversation memory
* Local LLM support through Ollama
* Docker Compose deployment
* CI/CD using GitHub Actions
* Production monitoring and logging

---

# 🎯 Assessment Requirements Coverage

| Requirement                | Implementation                      |
| -------------------------- | ----------------------------------- |
| CSV ingestion              | Pandas + SQLite ingestion service   |
| Queryable data             | SQLite database                     |
| Natural-language questions | Groq LLM                            |
| LLM integration            | Structured intent generation        |
| Query validation           | SQL/intent validator                |
| Anomaly detection          | Deterministic Python anomaly engine |
| REST API                   | FastAPI                             |
| `/query` endpoint          | Implemented                         |
| `/anomalies` endpoint      | Implemented                         |
| `/health` endpoint         | Implemented                         |
| Minimal UI                 | Streamlit                           |
| Testing                    | Pytest                              |
| Documentation              | README                              |
| No paid database           | SQLite                              |
| Python implementation      | Yes                                 |

---

# 🔗 API Architecture Summary

```text
                    ┌─────────────────────┐
                    │    Streamlit UI     │
                    └──────────┬──────────┘
                               │ HTTP
                               ▼
                    ┌─────────────────────┐
                    │    FastAPI REST     │
                    │        API          │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        Query Service    Anomaly Service    Health Route
              │                │
              ▼                ▼
          Groq LLM          Pandas
              │                │
              ▼                │
       Intent Validation       │
              │                │
              ▼                │
          SQLAlchemy           │
              │                │
              └───────┬────────┘
                      ▼
              ┌───────────────┐
              │     SQLite    │
              └───────────────┘
```

---

# 📌 Important Security Note

Do **not** commit your real Groq API key.

Your repository should contain:

```text
.env.example
```

but should **not** contain:

```text
.env
```

The `.env` file should be included in `.gitignore`.

---

# 👨‍💻 Author

**Aiman Parker**

AI/ML Engineer | Python | FastAPI | SQL | Machine Learning | AI Applications

---

# 📄 Assessment

Developed as part of the:

**End-to-End AI System Sprint — AI Engineer Technical Assessment**

Organization:

**DOTMappers IT Pvt. Ltd.**

The implementation focuses on building a practical, explainable, and maintainable AI system using Python, an LLM, REST APIs, structured database querying, anomaly detection, and a minimal user interface.

---

**One important thing before you push this:** your current project needs a small final cleanup to make the README match the repository exactly—especially `.gitignore`, `.env.example`, `requirements.txt` (the UI directly imports `requests`), and ideally a **single-command startup** script because the assessment specifically mentions that preference. We should do that before uploading the repo so the project manager can clone it and run it cleanly.
#   A I _ S U P P O R T - I N T E L L I G E N C E  
 