#!/bin/bash
# start.sh — Start the Ericsson GembaONE Platform
set -e
trap 'echo "Shutting down..."; [ -f .pids ] && while IFS= read -r pid; do kill "$pid" 2>/dev/null || true; done < .pids; rm -f .pids; exit 0' SIGINT SIGTERM

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Portable path conversion (for Git Bash on Windows)
native_path() {
    if command -v cygpath >/dev/null 2>&1; then
        cygpath -m "$1"
    else
        printf '%s' "$1"
    fi
}

# Port detection (lsof on macOS/Linux, netstat under Git Bash on Windows)
port_in_use() {
    if command -v lsof >/dev/null 2>&1; then
        lsof -iTCP:"$1" -sTCP:LISTEN -t >/dev/null 2>&1
    else
        netstat -an 2>/dev/null | grep -Eq "[:.]$1[[:space:]].*LISTEN"
    fi
}

find_available_port() {
    local port=$1
    while port_in_use "$port"; do
        echo "Port $port in use, trying $((port+1))..." >&2
        port=$((port+1))
    done
    echo $port
}

# === Prerequisite checks ===
check_prerequisites() {
    local errors=0
    echo "=== Checking prerequisites ==="

    # Python 3.11+ — probe by running it (python3 may be Windows Store stub under Git Bash)
    PYTHON=""
    for c in python3 python; do
        if "$c" -c 'import sys' >/dev/null 2>&1; then
            PYTHON=$c
            break
        fi
    done

    if [ -n "$PYTHON" ]; then
        PYTHON_VERSION=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
        PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
        if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
            echo "❌ Python 3.11+ required (found $PYTHON_VERSION)"
            errors=$((errors+1))
        else
            echo "✓ Python $PYTHON_VERSION"
        fi
    else
        echo "❌ Python 3 not found. Install from https://python.org"
        errors=$((errors+1))
    fi

    # Node.js 20+
    if command -v node &>/dev/null; then
        NODE_VERSION=$(node --version | sed 's/v//')
        NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d. -f1)
        if [ "$NODE_MAJOR" -lt 20 ]; then
            echo "❌ Node.js 20+ required (found $NODE_VERSION)"
            errors=$((errors+1))
        else
            echo "✓ Node.js $NODE_VERSION"
        fi
    else
        echo "❌ Node.js not found. Install from https://nodejs.org"
        errors=$((errors+1))
    fi

    # npm
    if ! command -v npm &>/dev/null; then
        echo "❌ npm not found"
        errors=$((errors+1))
    else
        echo "✓ npm $(npm --version)"
    fi

    # pip
    if [ -n "$PYTHON" ] && ! "$PYTHON" -m pip --version &>/dev/null; then
        echo "❌ pip not found. Run: $PYTHON -m ensurepip"
        errors=$((errors+1))
    fi

    if [ $errors -gt 0 ]; then
        echo ""
        echo "❌ $errors prerequisite(s) missing. Please install them and retry."
        exit 1
    fi
    echo ""
}

check_prerequisites

# === Stop previous run ===
if [ -f .pids ]; then
    echo "=== Stopping previous run ==="
    while IFS= read -r pid; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null && echo "  Stopped PID $pid" || true
        fi
    done < .pids
    rm -f .pids
    echo ""
fi

# === Setup backend ===
BACKEND_DIR="$SCRIPT_DIR/backend"
echo "=== Setting up backend ==="
cd "$BACKEND_DIR"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "  Creating Python virtual environment..."
    "$PYTHON" -m venv .venv
fi

# Activate venv (Windows: Scripts/activate, Unix: bin/activate)
if [ -f .venv/Scripts/activate ]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

# Copy dev.env to .env if missing
if [ ! -f .env ]; then
    echo "  Copying dev.env to .env..."
    cp dev.env .env
fi

# Install backend dependencies
echo "  Installing backend dependencies..."
pip install . -q

# Run Alembic migrations
echo "  Running database migrations..."
python -m alembic upgrade head

# Run seed data
echo "  Seeding database..."
python app/seed.py

# Find available backend port
BACKEND_PORT=$(find_available_port 9000)
echo "  Backend port: $BACKEND_PORT"

# Update CORS_ORIGINS in .env with frontend port
FRONTEND_PORT=$(find_available_port 5173)
echo "  Frontend port: $FRONTEND_PORT"

# Update CORS_ORIGINS in .env
if grep -q "^CORS_ORIGINS=" .env; then
    # Use python to update .env (portable across platforms)
    python -c "
import re
with open('.env', 'r') as f:
    content = f.read()
content = re.sub(r'^CORS_ORIGINS=.*$', 'CORS_ORIGINS=http://localhost:$FRONTEND_PORT', content, flags=re.MULTILINE)
with open('.env', 'w') as f:
    f.write(content)
" FRONTEND_PORT="$FRONTEND_PORT"
else
    echo "CORS_ORIGINS=http://localhost:$FRONTEND_PORT" >> .env
fi

# Export BACKEND_PORT for later use
export BACKEND_PORT

# Start backend
echo "  Starting backend on http://localhost:$BACKEND_PORT"
uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" &
BACKEND_PID=$!

cd "$SCRIPT_DIR"

# === Setup frontend ===
FRONTEND_DIR="$SCRIPT_DIR/frontend"
echo ""
echo "=== Setting up frontend ==="
cd "$FRONTEND_DIR"

# Install frontend dependencies
echo "  Installing frontend dependencies..."
npm ci

# Start frontend with BACKEND_PORT environment variable
echo "  Starting frontend on http://localhost:$FRONTEND_PORT"
BACKEND_PORT="$BACKEND_PORT" npm run dev -- --port "$FRONTEND_PORT" &
FRONTEND_PID=$!

cd "$SCRIPT_DIR"

# === Save PIDs ===
echo "$BACKEND_PID" > .pids
echo "$FRONTEND_PID" >> .pids

# === Print status ===
echo ""
echo "================================="
echo "=== GembaONE Platform Started ==="
echo "================================="
echo ""
echo "Backend:  http://localhost:$BACKEND_PORT"
echo "Frontend: http://localhost:$FRONTEND_PORT"
echo ""
echo "=== Seed Credentials ==="
echo "Admin:    admin@example.com / admin123"
echo "Engineer: engineer@example.com / engineer123"
echo "Reviewer: reviewer@example.com / reviewer123"
echo "ASP User: asp@example.com / asp123"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

wait
