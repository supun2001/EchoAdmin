# Admin AI Dashboard

A full-stack application for managing AI-powered email and voice interactions with a modern web interface.

## Features

- 📧 **Email AI Logs**: View and manage AI-generated email interactions
- 🎤 **Voice AI Logs**: View and manage voice call transcripts
- 🤖 **AI Integration**: Integrated with Google Gemini (email) and Deepgram (voice) agents
- 🗄️ **Database**: SQLite for development, PostgreSQL for production
- 🐳 **Docker Support**: Full containerization with docker-compose
- 🚀 **Production Ready**: Nginx reverse proxy and deployment configurations

## Project Structure

```
EchoAdmin/
├── backend/          # FastAPI backend
├── frontend/         # React frontend
├── email/            # Email AI agent
├── phone/            # Voice AI agent
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── nginx.conf
```

## Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)
- PostgreSQL (for production)

## Quick Start with Docker

1. **Clone the repository and navigate to the project directory**

2. **Create a `.env` file** (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env`** with your API keys and configuration:
   ```env
   DATABASE_URL=postgresql://adminai:adminai123@postgres:5432/admin_ai
   OPENAI_API_KEY=your_openai_api_key
   GEMINI_API_KEY=your_gemini_api_key
   DEEPGRAM_API_KEY=your_deepgram_api_key
   EMAIL=your-email@gmail.com
   GMAIL_PASSWORD=your_gmail_app_password
   ```

4. **Build and start all services**:
   ```bash
   docker-compose up --build
   ```

5. **Access the application**:
   - Frontend: http://localhost
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Local Development

### Backend

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables** (create `.env` file in project root):
   ```env
   DATABASE_URL=sqlite:///./admin_ai.db
   GEMINI_API_KEY=your_gemini_api_key
   DEEPGRAM_API_KEY=your_deepgram_api_key
   EMAIL=your-email@gmail.com
   GMAIL_PASSWORD=your_gmail_app_password
   ```

5. **Run the server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Create `.env` file** (optional, for custom API URL):
   ```env
   VITE_API_URL=http://localhost:8000/api
   ```

4. **Run the development server**:
   ```bash
   npm run dev
   ```

5. **Access the application**: http://localhost:5173

## API Endpoints

### Email Endpoints

- `GET /api/email/logs` - Get paginated email logs
  - Query params: `page`, `page_size`
- `GET /api/email/log/{id}` - Get single email log
- `POST /api/send-email` - Send email using AI agent
  - Query params: `to_email`, `subject`, `body`, `custom_instruction`

### Voice Endpoints

- `GET /api/voice/logs` - Get paginated voice logs
  - Query params: `page`, `page_size`
- `GET /api/voice/log/{id}` - Get single voice log with transcript
- `POST /api/upload-audio` - Upload and process audio file
  - Form data: `file`, `phone_number` (optional)

## Deployment

### Option 1: Docker Compose on VPS (Ubuntu)

1. **SSH into your VPS**:
   ```bash
   ssh user@your-server-ip
   ```

2. **Install Docker and Docker Compose**:
   ```bash
   sudo apt update
   sudo apt install docker.io docker-compose -y
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

3. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd EchoAdmin
   ```

4. **Create `.env` file** with production values:
   ```env
   DATABASE_URL=postgresql://adminai:strong_password@postgres:5432/admin_ai
   POSTGRES_PASSWORD=strong_password
   # ... other environment variables
   ```

5. **Build and start**:
   ```bash
   docker-compose up -d --build
   ```

6. **Set up Nginx reverse proxy** (if not using Docker nginx):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:80;
       }
       
       location /api {
           proxy_pass http://localhost:8000;
       }
   }
   ```

### Option 2: Render

1. **Backend Service**:
   - Build Command: `cd backend && pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Environment Variables: Add all from `.env.example`

2. **Frontend Service**:
   - Build Command: `cd frontend && npm install && npm run build`
   - Publish Directory: `frontend/dist`
   - Environment Variables: `VITE_API_URL=https://your-backend.onrender.com/api`

3. **PostgreSQL Database**:
   - Create a PostgreSQL database on Render
   - Update `DATABASE_URL` in backend environment variables

### Option 3: Railway

1. **Create `railway.json`**:
   ```json
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {
       "builder": "DOCKERFILE",
       "dockerfilePath": "Dockerfile.backend"
     },
     "deploy": {
       "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 10
     }
   }
   ```

2. **Deploy via Railway CLI**:
   ```bash
   railway login
   railway init
   railway up
   ```

3. **Add environment variables** in Railway dashboard

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Yes (for voice) |
| `GEMINI_API_KEY` | Google Gemini API key | Yes (for email) |
| `DEEPGRAM_API_KEY` | Deepgram API key | Yes (for voice) |
| `EMAIL` | Gmail address for sending emails | Yes |
| `GMAIL_PASSWORD` | Gmail app password | Yes |
| `VITE_API_URL` | Backend API URL (frontend) | No |

## Database Migrations

The application uses SQLAlchemy with automatic table creation. For production, consider using Alembic for migrations:

```bash
# Install Alembic
pip install alembic

# Initialize
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

## Troubleshooting

### Backend won't start
- Check database connection string
- Verify all environment variables are set
- Check logs: `docker-compose logs backend`

### Frontend can't connect to API
- Verify `VITE_API_URL` is set correctly
- Check CORS settings in backend
- Ensure backend is running on correct port

### Database connection errors
- Verify PostgreSQL is running: `docker-compose ps`
- Check database credentials in `.env`
- Ensure database exists

## License

MIT

## Support

For issues and questions, please open an issue on GitHub.
