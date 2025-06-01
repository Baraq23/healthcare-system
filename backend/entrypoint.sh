#!/bin/bash

# Wait for MySQL
while ! nc -z mysql 3306; do
  echo "Waiting for MySQL..."
  sleep 2
done

# Initialize database
python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"

# Start FastAPI - CORRECTED COMMAND
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4