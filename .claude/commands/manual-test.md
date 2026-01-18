# Manual Test Environment

Start the backend server and frontend app for manual testing.

## Instructions

Execute the following steps in order:

### Step 1: Stop any existing processes

Kill any running backend or frontend processes:

```bash
# Kill existing uvicorn/python processes on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Kill any existing Vite dev server on port 5173
lsof -ti:5173 | xargs kill -9 2>/dev/null || true
```

### Step 2: Start the backend server

Start the FastAPI backend server in the background:

```bash
cd /Users/howie/Workspace/github/voice-lab/backend && \
nohup uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/voice-lab_backend.log 2>&1 &
```

Wait and verify the server is running:

```bash
sleep 3 && curl -s http://localhost:8000/health
```

Expected output: `{"status":"healthy",...}`

### Step 3: Start the frontend dev server

Start the React frontend in the background:

```bash
cd /Users/howie/Workspace/github/voice-lab/frontend && \
nohup npm run dev > /tmp/voice-lab_frontend.log 2>&1 &
```

Wait and verify:

```bash
sleep 3 && curl -s http://localhost:5173 | head -5
```

### Step 4: Open in browser

```bash
open http://localhost:5173
```

## API Endpoints for Testing

### Health Check
```bash
curl -s http://localhost:8000/health | jq
```

### TTS Synthesis (batch mode)
```bash
curl -X POST http://localhost:8000/api/v1/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，這是語音測試",
    "provider": "azure",
    "voice_id": "zh-TW-HsiaoChenNeural",
    "language": "zh-TW"
  }' | jq '.duration_ms, .latency_ms'
```

### List Voices
```bash
curl -s "http://localhost:8000/api/v1/voices?provider=azure&language=zh-TW" | jq
```

### List Providers
```bash
curl -s http://localhost:8000/api/v1/tts/providers | jq
```

## Logs

- Backend logs: `tail -f /tmp/voice-lab_backend.log`
- Frontend logs: `tail -f /tmp/voice-lab_frontend.log`

## Cleanup

To stop everything:

```bash
# Stop backend
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Stop frontend
lsof -ti:5173 | xargs kill -9 2>/dev/null || true
```

## Quick Start (All-in-one)

Run everything in one command:

```bash
# Cleanup
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true

# Start backend
cd /Users/howie/Workspace/github/voice-lab/backend && \
nohup uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/voice-lab_backend.log 2>&1 &

# Start frontend
cd /Users/howie/Workspace/github/voice-lab/frontend && \
nohup npm run dev > /tmp/voice-lab_frontend.log 2>&1 &

# Wait and verify
sleep 4
echo "=== Backend Health ===" && curl -s http://localhost:8000/health | jq
echo "=== Frontend ===" && curl -s -o /dev/null -w "%{http_code}" http://localhost:5173

# Open browser
open http://localhost:5173
```

## Environment Variables

Make sure these are set for TTS providers:

```bash
# Azure
export AZURE_SPEECH_KEY="your-key"
export AZURE_SPEECH_REGION="eastasia"

# Google Cloud
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

# ElevenLabs
export ELEVENLABS_API_KEY="your-key"
```

## Verification Checklist

After both services are running:

- [ ] Backend health: `curl http://localhost:8000/health` returns healthy
- [ ] Frontend loads: `http://localhost:5173` shows the UI
- [ ] TTS test: Can synthesize speech via API or UI
- [ ] Voice list: Can fetch available voices
- [ ] Provider comparison: Can compare multiple TTS providers
