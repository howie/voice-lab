# Quickstart: Pipecat TTS Server

**Feature**: `001-pipecat-tts-server`

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional)
- API Keys for:
  - Azure Speech Services
  - Google Cloud TTS
  - ElevenLabs

## Setup

### 1. Backend Setup

1. Navigate to backend:
   ```bash
   cd backend
   ```

2. Create virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -e .[dev]
   ```
   *Note: This will install `fastapi`, `pipecat-ai`, and provider SDKs.*

3. Configure Environment:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

4. Run Database Migrations:
   ```bash
   alembic upgrade head
   ```

5. Start Server:
   ```bash
   uvicorn src.main:app --reload
   ```
   API Docs available at `http://localhost:8000/docs`

### 2. Frontend Setup

1. Navigate to frontend:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start Dev Server:
   ```bash
   npm run dev
   ```
   Access Web Interface at `http://localhost:5173`

## Usage Examples

### Synthesize Speech (cURL)

```bash
curl -X POST "http://localhost:8000/api/v1/tts/synthesize" \
     -H "Content-Type: application/json" \
     -d 
'{ "text": "Hello from Voice Lab", "provider": "gcp", "voice_id": "en-US-Standard-A" }'
     --output output.mp3
```

### List Voices (cURL)

```bash
curl "http://localhost:8000/api/v1/tts/voices?language=en-US"
```