# Suno AI API Research

> Research Date: 2026-01-30

## Overview

**Suno AI does not currently offer an official public API.** All "Suno API" integrations in the ecosystem rely on **unofficial third-party proxy services** or **open-source reverse-engineering projects** that wrap Suno's internal web endpoints. Suno has indicated official developer tools are "in development" but has not announced a timeline or public beta.

## API Access Methods

### A. Open-Source Wrappers (Cookie-Based)

Projects like `gcui-art/suno-api` and `Malith-Rukshan/Suno-API` authenticate by extracting session cookies from a logged-in browser session at `suno.com`.

- Set via `SUNO_COOKIE` environment variable
- Requires `TWOCAPTCHA_KEY` for hCaptcha challenges
- Cookies expire periodically and require manual refresh

### B. Third-Party Proxy Services (API Key)

Services like SunoAPI.org, GoAPI, PiAPI, and Apiframe issue their own API keys:

```
Authorization: Bearer <third-party-api-key>
```

These services act as middlemen between your application and Suno's internal endpoints.

## Known Endpoints (Unofficial)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/generate` | POST | Simple mode: generate from text prompt |
| `/api/custom_generate` | POST | Custom mode: explicit lyrics, style, title |
| `/api/generate_lyrics` | POST | Generate lyrics from prompt |
| `/api/extend_audio` | POST | Extend existing clip duration |
| `/api/concat` | POST | Assemble full song from multiple extensions |
| `/api/generate_stems` | POST | Separate track into stems |
| `/api/get` | GET | Retrieve clip(s) by ID |
| `/api/get_limit` | GET | Check account credits/quota |
| `/api/clip` | GET | Retrieve clip data by ID |
| `/api/get_aligned_lyrics` | GET | Word-level lyric timestamps |

## Request/Response Format

### Custom Mode Request

```json
{
  "prompt": "[Verse]\nI found a love, for me\nDarling, just dive right in...",
  "tags": "pop, romantic ballad, acoustic guitar",
  "title": "Perfect Harmony",
  "make_instrumental": false,
  "is_custom": true,
  "model_version": "chirp-crow",
  "wait_audio": true
}
```

### Simple Mode Request

```json
{
  "prompt": "An upbeat electronic dance track with synth leads",
  "make_instrumental": false,
  "wait_audio": false
}
```

### Clip Response Object

```json
{
  "id": "abc123-uuid",
  "title": "Perfect Harmony",
  "audio_url": "https://cdn1.suno.ai/abc123-uuid.mp3",
  "video_url": "https://cdn1.suno.ai/abc123-uuid.mp4",
  "image_url": "https://cdn2.suno.ai/image_abc123.jpeg",
  "major_model_version": "v5",
  "model_name": "chirp-crow",
  "status": "complete",
  "metadata": {
    "tags": "pop, romantic ballad, acoustic guitar",
    "prompt": "[Verse]\nI found a love...",
    "duration": 180.5
  },
  "created_at": "2026-01-30T10:00:00Z"
}
```

Each generation returns **2 clips** (two variations).

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `prompt` | string | Text description or lyrics (max 500 chars simple; full custom) |
| `tags` / `style` | string | Genre/style (max 200 chars v4, 1000 chars v4.5+) |
| `title` | string | Track name (required in custom mode) |
| `make_instrumental` | boolean | Instrumental only (default: false) |
| `is_custom` | boolean | Custom mode (default: false) |
| `model_version` | string | Model ID (see below) |
| `wait_audio` | boolean | Block until audio ready (default: false) |
| `continue_clip_id` | string | Clip ID for extension |
| `continue_at` | number | Timestamp (seconds) for extension |
| `callBackUrl` | string | Webhook URL (third-party only) |

## Models

| Model ID | Version | Max Duration | Notes |
|----------|---------|-------------|-------|
| `chirp-crow` | v5 | TBD | Latest, studio-grade fidelity |
| `chirp-bluejay` | v4.5+ | 8 min | Enhanced prompt understanding |
| `chirp-auk` | v4.5 | 8 min | Faster generation |
| `chirp-v4` | v4 | 4 min | Major vocal upgrade |
| `chirp-v3-5` | v3.5 | 4 min | Deprecated Sept 2025 |

## Async Pattern

```
1. POST /api/generate or /api/custom_generate
   -> Returns clip IDs (audio_url present if wait_audio=true)

2. If wait_audio=false, poll:
   GET /api/get?ids=clip_id_1,clip_id_2
   -> status: "submitted" -> "queued" -> "streaming" -> "complete"
   -> audio_url populated when status = "complete"
```

Webhook callbacks (third-party only) provide stages: `text`, `first`, `complete`.

## Pricing

| Plan | Price | Credits/Month |
|------|-------|---------------|
| Free | $0 | 50/day |
| Pro | ~$8/month | 2,500 |
| Premier | ~$24/month | 10,000 |

Each generation = 10 credits (2 clips). Third-party API pricing: ~$0.01-$0.04/call.

## Output Formats

- **MP3**: Default, 320kbps (all tiers)
- **WAV**: Lossless (Pro/Premier subscribers only)
- **MP4**: Audio with visualisation

## Unofficial Python Libraries

```python
# SunoAI package (Malith-Rukshan)
from suno import Suno, ModelVersions

client = Suno(cookie='YOUR_COOKIE', model_version=ModelVersions.CHIRP_V3_5)
songs = client.generate(
    prompt="A serene landscape",
    is_custom=False,
    wait_audio=True,
)
```

## Key Risks

1. **No official API** -- all access is unofficial, can break anytime
2. **TOS violation risk** -- cookie scraping likely violates Suno's Terms of Service
3. **CAPTCHA dependency** -- requires paid CAPTCHA-solving services
4. **Commercial licensing uncertainty** -- unclear rights for content generated via unofficial APIs
5. **No SLA or support** -- third-party services have no uptime guarantees
6. **Auth fragility** -- session cookies expire and need manual refresh

## Sources

- [gcui-art/suno-api (GitHub)](https://github.com/gcui-art/suno-api)
- [Malith-Rukshan/Suno-API (GitHub)](https://github.com/Malith-Rukshan/Suno-API)
- [SunoAPI.org Documentation](https://docs.sunoapi.org)
- [AIML API - Suno AI API](https://aimlapi.com/suno-ai-api)
- [Suno Model Timeline (Official)](https://help.suno.com/en/articles/5782721)
- [Evolink - Suno API Review 2026](https://evolink.ai/en/blog/suno-api-review-complete-guide-ai-music-generation-integration)
