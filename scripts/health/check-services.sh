#!/bin/bash

# Health check script for all services
echo "🏥 Checking service health..."

# Check Caddy
echo "Checking Caddy..."
if curl -s -f http://localhost:80 > /dev/null; then
    echo "  ✅ Caddy is healthy"
else
    echo "  ❌ Caddy is not responding"
fi

# Check backend
echo "Checking Backend..."
if curl -s -f http://localhost:8000/health > /dev/null; then
    echo "  ✅ Backend is healthy"
else
    echo "  ❌ Backend is not responding"
fi

# Check frontend
echo "Checking Frontend..."
if curl -s -f http://localhost:3000 > /dev/null; then
    echo "  ✅ Frontend is healthy"
else
    echo "  ❌ Frontend is not responding"
fi

# Check Temporal
echo "Checking Temporal..."
if curl -s -f http://localhost:8080 > /dev/null; then
    echo "  ✅ Temporal UI is healthy"
else
    echo "  ❌ Temporal UI is not responding"
fi

# Check PostgreSQL
echo "Checking PostgreSQL..."
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "  ✅ PostgreSQL is healthy"
else
    echo "  ❌ PostgreSQL is not responding"
fi

# Check Redis
echo "Checking Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo "  ✅ Redis is healthy"
else
    echo "  ❌ Redis is not responding"
fi

echo "🏥 Health check completed"
