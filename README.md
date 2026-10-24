# Log Intelligence

A backend application for uploading, parsing, and analyzing application logs through a REST API.

## Features

- Upload log files through a FastAPI endpoint.
- Parse log entries and identify severity levels.
- Perform rule-based log analysis and severity assessment.
- Create analysis jobs and track their processing status.
- Store job information and analysis results in PostgreSQL.
- Use asynchronous SQLAlchemy sessions for database access.
- Manage database schema changes with Alembic.
- Run automated tests with pytest.

## Technology Stack

- **Language:** Python
- **API:** FastAPI
- **Validation:** Pydantic
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy (async)
- **Migrations:** Alembic
- **Testing:** pytest
- **Infrastructure:** Docker Compose
- **CI:** GitHub Actions

## Project Structure

```text
log-intelligence/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── db.py
│   │   ├── init_db.py
│   │   ├── main.py
│   │   └── models.py
│   ├── migrations/
│   └── tests/
├── .github/
│   └── workflows/
├── data/
├── .env.example
├── alembic.ini
├── docker-compose.yml
├── pytest.ini
└── README.md
```

## Prerequisites

- Python 3.12 or a compatible version supported by the dependencies.
- PostgreSQL, or Docker with Docker Compose.
- Git.

## Local Setup

1. Clone the repository and enter the project directory.

   ```bash
   git clone <your-repository-url>
   cd log-intelligence
   ```

2. Create and activate a virtual environment.

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies.

   ```bash
   pip install -r backend/requirements.txt
   ```

4. Create a local environment file using the example.

   ```bash
   cp .env.example .env
   ```

5. Update `.env` with your local database connection settings. Never commit `.env` or real credentials.

6. Start PostgreSQL using your configured local setup or Docker Compose.

7. Apply database migrations.

   ```bash
   alembic upgrade head
   ```

8. Start the API.

   ```bash
   uvicorn app.main:app --app-dir backend --reload
   ```

The interactive API documentation is available at `http://127.0.0.1:8000/docs`.

## Run Tests

From the project root, with the virtual environment activated:

```bash
pytest -q
```

## Database Migrations

Create a migration after changing the database models:

```bash
alembic revision --autogenerate -m "describe your change"
```

Review the generated migration before applying it:

```bash
alembic upgrade head
```

## Security Notes

- Keep `.env` and credentials out of version control.
- Validate uploaded files and handle malformed input safely.
- Restrict database access to authorized application users.
- Configure production secrets and database connections outside source code.

## Current Scope

This project currently focuses on log ingestion, parsing, analysis jobs, and API-level job status and result retrieval. Authentication, incident-management endpoints, and durable background-worker processing are potential future enhancements.

## License

No license has been selected yet.
