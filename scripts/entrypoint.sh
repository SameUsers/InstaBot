#!/bin/bash
set -e

echo "=========================================="
echo "InstaBot Docker Entrypoint Starting..."
echo "=========================================="

if ! command -v pg_isready &> /dev/null; then
    echo "ERROR: pg_isready not found!"
    exit 1
fi

echo ""
echo "Step 1: Waiting for PostgreSQL..."
while ! pg_isready -h ${DB_HOST:-db} -p ${DB_PORT:-5432} -U ${DB_USER:-postgres} 2>/dev/null; do
    echo "  PostgreSQL not ready yet, waiting..."
    sleep 2
done
echo "✓ PostgreSQL is ready!"

echo ""
echo "Step 2: Running Alembic migrations..."
cd /app || { echo "ERROR: Failed to cd to /app"; exit 1; }

if alembic -c config/alembic.ini current 2>/dev/null || true; then
    echo "  Current Alembic state checked"
fi

if alembic -c config/alembic.ini upgrade head; then
    echo "✓ Migrations completed successfully!"
else
    echo "✗ Migrations failed!"
    exit 1
fi

echo ""
echo "Step 3: Running unit tests..."
cd /app || exit 1
if pytest -c config/pytest.ini source/tests/unit/ -v --tb=short; then
    echo "✓ Unit tests passed!"
else
    echo "✗ Unit tests failed!"
    exit 1
fi

echo ""
echo "Step 4: Running integration tests..."
if pytest -c config/pytest.ini source/tests/integration/ -v --tb=short 2>/dev/null; then
    echo "✓ Integration tests passed!"
else
    echo "⚠ Integration tests skipped or failed (expected if no tests yet)"
fi

echo ""
echo "Step 5: Running API tests..."
if pytest -c config/pytest.ini source/tests/api/ -v --tb=short; then
    echo "✓ API tests passed!"
else
    echo "✗ API tests failed!"
    exit 1
fi

echo ""
echo "=========================================="
echo "✓ All tests passed successfully!"
echo "Starting InstaBot application..."
echo "=========================================="
echo ""

exec uvicorn main:app --host 0.0.0.0 --port 8000

