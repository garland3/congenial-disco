# Multi-stage Docker build for AI Interview Assistant
FROM node:18-alpine AS frontend-builder

# Set working directory for frontend build
WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install frontend dependencies
RUN npm install

# Copy frontend source code
COPY frontend/ ./

# Build the frontend
RUN npm run build

# Production stage - Python base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements first for better caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend from frontend-builder stage
COPY --from=frontend-builder /app/frontend/dist ./backend/static

# Create directory for SQLite database
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONPATH=/app/backend
ENV DATABASE_URL=sqlite:////app/data/interview_app.db

# Expose port
EXPOSE 8000

# Create a startup script that serves both frontend and backend
RUN echo '#!/bin/bash\n\
cd /app/backend\n\
uvicorn app.main:app --host 0.0.0.0 --port 8000' > /app/start.sh && \
chmod +x /app/start.sh

# Update FastAPI main.py to serve static files
RUN echo 'from fastapi import FastAPI\n\
from fastapi.middleware.cors import CORSMiddleware\n\
from fastapi.staticfiles import StaticFiles\n\
from fastapi.responses import FileResponse\n\
from .database import create_tables\n\
from .routes import admin, interview\n\
import os\n\
\n\
app = FastAPI(\n\
    title="AI Interview Assistant",\n\
    description="FastAPI backend for AI-powered interview system",\n\
    version="1.0.0"\n\
)\n\
\n\
app.add_middleware(\n\
    CORSMiddleware,\n\
    allow_origins=["*"],\n\
    allow_credentials=True,\n\
    allow_methods=["*"],\n\
    allow_headers=["*"],\n\
)\n\
\n\
app.include_router(admin.router)\n\
app.include_router(interview.router)\n\
\n\
# Mount static files for frontend\n\
static_dir = os.path.join(os.path.dirname(__file__), "static")\n\
if os.path.exists(static_dir):\n\
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")\n\
    \n\
    @app.get("/{full_path:path}")\n\
    def serve_frontend(full_path: str):\n\
        # Serve API routes normally\n\
        if full_path.startswith(("docs", "openapi.json", "admin", "interview")):\n\
            return {"message": "API route"}\n\
        \n\
        # Serve index.html for all other routes (SPA)\n\
        index_file = os.path.join(static_dir, "index.html")\n\
        if os.path.exists(index_file):\n\
            return FileResponse(index_file)\n\
        return {"message": "Frontend not built"}\n\
\n\
@app.on_event("startup")\n\
def startup_event():\n\
    create_tables()\n\
\n\
@app.get("/api")\n\
def read_root():\n\
    return {"message": "AI Interview Assistant API", "docs": "/docs"}' > /app/backend/app/main_docker.py

# Command to run the application
CMD ["/app/start.sh"]