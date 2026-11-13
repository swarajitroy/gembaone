# Ericsson GembaONE Platform

AI-assisted, human-accountable web platform for structured field data capture and auditable Excel-based data ingestion.

## Overview

The Ericsson GembaONE Platform enables:
- **Field Survey Checklists**: Versioned templates with conditional logic, photo/location capture, and structured submission workflow
- **Excel Ingestion Engine**: Upload, validate, and commit Excel data with layered validation, row-level results, and audit trails
- **Role-Based Access Control**: Internal admin, field engineer, reviewer, and ASP (external service provider) roles with permission enforcement

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: SQLite (local), PostgreSQL (production)
- **ORM**: SQLAlchemy with Alembic migrations
- **Authentication**: JWT tokens with bcrypt password hashing
- **API**: RESTful endpoints under `/api/v1`

### Frontend
- **Framework**: React + TypeScript
- **Build Tool**: Vite
- **Design System**: IBM Carbon Design System
- **Styling**: Tailwind CSS + Carbon styles
- **State Management**: React Context + hooks
- **E2E Testing**: Playwright

### Storage
- **Local Development**: File-based object storage emulation in `backend/uploads/`
- **Production**: Cloud object storage (S3/Azure Blob/GCS) via adapter pattern

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- npm

### Local Development (Recommended)

Start both backend and frontend services with one command:

```bash
./start.sh
```

Or on Windows:
```cmd
start.bat
```

This script will:
1. Check prerequisites (Python 3.11+, Node.js 20+)
2. Create backend virtual environment
3. Install backend dependencies
4. Run database migrations
5. Seed demo data
6. Start backend on http://localhost:9000 (or next available port)
7. Install frontend dependencies
8. Start frontend on http://localhost:5173 (or next available port)

**Stop services:**
```bash
./stop.sh
```

### Docker Compose (SQLite)

Build and run with Docker:

```bash
docker compose build
docker compose up
```

The application will be accessible at:
- Frontend: http://localhost (port 80)
- Backend: http://localhost:9000

**Stop services:**
```bash
docker compose down
```

### Docker Compose (PostgreSQL)

For production-like deployment with PostgreSQL:

```bash
docker compose -f docker-compose.yml -f docker-compose.postgres.yml build
docker compose -f docker-compose.yml -f docker-compose.postgres.yml up
```

**Stop services:**
```bash
docker compose -f docker-compose.yml -f docker-compose.postgres.yml down
```

## Seed Credentials

The application comes with pre-seeded demo users for each role:

| Role | Email | Password | Description |
|------|-------|----------|-------------|
| **Admin** | `admin@example.com` | `admin123` | Internal administrator with full access |
| **Engineer** | `engineer@example.com` | `engineer123` | Field engineer (create/submit checklists) |
| **Reviewer** | `reviewer@example.com` | `reviewer123` | Reviewer (view submitted checklists) |
| **ASP User** | `asp@example.com` | `asp123` | External service provider (limited to own ingestions) |

All passwords use the same format for demo purposes. In production, use strong passwords and secure credential management.

## Running Tests

### Backend Tests

From the `backend/` directory:

```bash
# Activate virtual environment
source .venv/bin/activate  # Unix/macOS
# or
.venv\Scripts\activate     # Windows

# Run all tests
pytest

# Run specific test files
pytest tests/test_auth_service.py

# Run with coverage
pytest --cov=app --cov-report=html
```

### Frontend Tests

From the `frontend/` directory:

```bash
# Unit tests (vitest)
npm test

# E2E tests (Playwright)
npx playwright test

# E2E tests in headed mode
npx playwright test --headed

# E2E tests for specific file
npx playwright test e2e/wireframe_01_login.spec.ts
```

## Project Structure

```
gembaone/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── repositories/    # Database access layer
│   │   ├── services/        # Business logic
│   │   ├── routers/         # API endpoints
│   │   ├── middleware/      # Auth, logging, correlation IDs
│   │   └── adapters/        # External system integrations
│   ├── alembic/             # Database migrations
│   ├── tests/               # Backend tests
│   ├── pyproject.toml       # Python dependencies
│   └── dev.env              # Local development config
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── lib/             # Utilities and API client
│   │   └── types/           # TypeScript interfaces
│   ├── e2e/                 # Playwright E2E tests
│   └── package.json         # Node dependencies
├── shared_config.json       # Shared frontend/backend config
├── docker-compose.yml       # Docker compose (SQLite)
├── docker-compose.postgres.yml  # PostgreSQL override
├── start.sh                 # Local development launcher
├── stop.sh                  # Stop local services
├── start.bat                # Windows launcher (Git Bash wrapper)
└── README.md                # This file
```

## API Documentation

When the backend is running, API documentation is available at:
- **Swagger UI**: http://localhost:9000/docs
- **ReDoc**: http://localhost:9000/redoc
- **OpenAPI JSON**: http://localhost:9000/openapi.json

## Key Features

### Checklist Management
- **Templates**: Version-controlled checklist templates with conditional items
- **Instances**: Create checklist instances from published templates
- **Answers**: Capture structured answers with type validation (text, number, boolean, date, JSON)
- **Evidence**: Upload photos and files as evidence for checklist items
- **Location**: Capture GPS coordinates at instance or item level
- **Submission**: Submit checklists with validation of required visible items

### Excel Ingestion
- **Upload**: Upload Excel `.xlsx` files with mapping to target schema
- **Validation**: Layered validation (structural → schema → business rules → warnings)
- **Results**: Row-level results with accepted/rejected/warning outcomes
- **Reports**: Downloadable CSV reports with validation details
- **Audit**: Complete audit trail of ingestion lifecycle

### Security & Compliance
- **Authentication**: JWT-based authentication with bcrypt password hashing
- **Authorization**: Role-based access control enforced at service layer
- **Audit Logging**: All compliance-relevant actions logged with correlation IDs
- **ASP Restrictions**: External service providers cannot delete or access other users' data

## Development

### Adding New Endpoints

See [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md) for detailed instructions on:
- Adding new mapping versions
- Activating mappings
- Adding validation rule types
- Regenerating seed data

### Environment Variables

Backend configuration (see `backend/dev.env`):
- `DATABASE_URL`: Database connection string (default: `sqlite:///./app.db`)
- `SECRET_KEY`: JWT signing secret
- `JWT_ALGORITHM`: JWT algorithm (default: `HS256`)
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiry (default: `1440` = 24 hours)
- `CORS_ORIGINS`: Allowed CORS origins (comma-separated)
- `ENVIRONMENT`: Environment name (`development`, `staging`, `production`)
- `RATE_LIMIT_ENABLED`: Enable/disable rate limiting (default: `true`)

### Database Migrations

Create a new migration after modifying models:

```bash
cd backend
source .venv/bin/activate
alembic revision --autogenerate -m "description of changes"
alembic upgrade head
```

## Deployment

### Production Considerations

1. **Database**: Use PostgreSQL instead of SQLite
   - Set `DATABASE_URL` to PostgreSQL connection string
   - Ensure `psycopg[binary]>=3.2` is installed (included in `[postgres]` optional dependencies)

2. **Secrets Management**:
   - Generate strong `SECRET_KEY` (min 32 characters)
   - Use environment-specific secrets management (AWS Secrets Manager, Azure Key Vault, etc.)
   - Never commit production credentials

3. **CORS**: Update `CORS_ORIGINS` to include only your production domains

4. **Object Storage**: Configure cloud object storage adapter (S3/Azure Blob/GCS)

5. **Monitoring**: Enable application monitoring and logging

### Docker Production Build

```bash
# Build images
docker compose -f docker-compose.yml -f docker-compose.postgres.yml build

# Run with production config
docker compose -f docker-compose.yml -f docker-compose.postgres.yml up -d
```

## Contributing

1. **Code Style**: Follow PEP 8 (Python) and ESLint rules (TypeScript)
2. **Testing**: Write tests for new features
3. **Commits**: Use conventional commit messages (`feat:`, `fix:`, `test:`, `docs:`, etc.)
4. **Reviews**: All changes reviewed before merge

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (need 3.11+)
- Check virtual environment is activated
- Check database file permissions
- Check logs for specific error messages

### Frontend won't start
- Check Node version: `node --version` (need 20+)
- Delete `node_modules` and run `npm install` again
- Check backend is running and accessible
- Check browser console for errors

### Tests failing
- Ensure database is seeded: `python app/seed.py` (backend)
- Check virtual environment has all dependencies installed
- Run tests individually to isolate failures
- Check test database is clean (tests use separate test database)

### Docker build fails
- Check Docker is installed and running
- Check disk space
- Try: `docker system prune -a` to clean up old images
- Check Dockerfile and docker-compose.yml syntax

## License

Internal Ericsson project. All rights reserved.

## Support

For issues or questions, contact the GembaONE Platform development team.
