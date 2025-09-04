# AI Interview Assistant

A FastAPI backend with React frontend for conducting AI-powered interviews. The system allows admins to create interview templates and users to take structured interviews with AI guidance.

## Features

- **Admin Dashboard**: Create and manage interview templates
- **AI Template Generation**: Generate interview questions from goals using OpenRouter/OpenAI compatible LLM
- **Interactive Interviews**: Users can take interviews with real-time AI evaluation
- **Progress Tracking**: Visual progress bars and session status
- **Data Export**: Export interview results as JSON

## Architecture

- **Backend**: FastAPI with SQLAlchemy, OpenAI-compatible LLM integration
- **Frontend**: React with TypeScript, Tailwind CSS, React Router
- **Database**: SQLite (configurable to PostgreSQL/MySQL)
- **LLM Provider**: OpenRouter (configurable to any OpenAI-compatible API)

## Setup

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn
- Docker (optional, for containerized deployment)

### Development Setup (Local)

#### Option 1: Quick Start Script
You can use the provided startup script to set up and run both backend and frontend:
```bash
chmod +x start.sh
./start.sh
```

#### Option 2: Manual Setup

**Backend Setup:**
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create environment file:
   ```bash
   cp .env.example .env
   ```

5. Edit `.env` with your OpenRouter API key:
   ```bash
   OPENROUTER_API_KEY=your_api_key_here
   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
   MODEL_NAME=openai/gpt-3.5-turbo
   DATABASE_URL=sqlite:///./interview_app.db
   ```

6. Start the backend server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

**Frontend Setup:**
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

### Docker Deployment

#### Build and run with Docker:
```bash
# Build the Docker image
docker build -t ai-interview-assistant .

# Run the container
docker run -p 8000:8000 \
  -e OPENROUTER_API_KEY=your_api_key_here \
  -e OPENROUTER_BASE_URL=https://openrouter.ai/api/v1 \
  -e MODEL_NAME=openai/gpt-3.5-turbo \
  ai-interview-assistant
```

#### Using Docker Compose (recommended):
Create a `docker-compose.yml` file:
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
      - MODEL_NAME=openai/gpt-3.5-turbo
      - DATABASE_URL=sqlite:///./interview_app.db
    volumes:
      - ./data:/app/data  # Optional: persist database
```

Then run:
```bash
# Set your API key
export OPENROUTER_API_KEY=your_api_key_here

# Start the application
docker-compose up -d
```

The application will be available at:
- **Frontend & API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Usage

1. **Access the application**: Open http://localhost:5173 in your browser

2. **Create interview templates**: 
   - Go to the Admin section
   - Click "Generate Template" 
   - Describe your interview goals
   - The AI will create relevant questions

3. **Take interviews**:
   - Go to the Interviews section
   - Select a template
   - Answer questions as prompted by the AI
   - Export your results when complete

## API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation.

## Configuration

### Environment Variables

- `OPENROUTER_API_KEY`: Your OpenRouter API key
- `OPENROUTER_BASE_URL`: API base URL (default: https://openrouter.ai/api/v1)
- `MODEL_NAME`: Model to use (default: openai/gpt-3.5-turbo)
- `DATABASE_URL`: Database connection string

### Supported LLM Providers

The system works with any OpenAI-compatible API:
- OpenRouter
- OpenAI directly
- Local models (via OpenAI-compatible servers)
- Azure OpenAI
- Other compatible providers

## Development

### Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── models.py            # Database models and Pydantic schemas
│   │   ├── database.py          # Database configuration
│   │   ├── config.py            # Application settings
│   │   ├── routes/
│   │   │   ├── admin.py         # Admin API endpoints
│   │   │   └── interview.py     # Interview API endpoints
│   │   └── services/
│   │       └── llm_service.py   # LLM integration service
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── api/                 # API client
│   │   └── App.tsx              # Main application
│   └── package.json
└── old/                         # Original demo HTML file
```

### Adding New Features

1. **Backend**: Add new endpoints in `routes/`, create services in `services/`
2. **Frontend**: Add new components in `components/`, update API client as needed

## License

MIT License