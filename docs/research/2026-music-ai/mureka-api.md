# Mureka AI API Research

> Research Date: 2026-01-30

## Overview

Mureka AI provides an **official, documented REST API** for music generation at `api.mureka.ai`. The API is developed by Skywork AI (a Kunlun Tech subsidiary) and serves nearly 10 million users. It offers song generation, instrumental/BGM, lyrics, stem separation, and song analysis.

**Official Docs**: [platform.mureka.ai/docs](https://platform.mureka.ai/docs/)

## Authentication

Bearer Token via API key created at [platform.mureka.ai/apiKeys](https://platform.mureka.ai/apiKeys):

```
Authorization: Bearer $MUREKA_API_KEY
```

## Endpoints

### Music Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/song/generate` | Generate song with vocals |
| GET | `/v1/song/query/{task_id}` | Poll song generation status |
| POST | `/v1/instrumental/generate` | Generate instrumental/BGM |
| GET | `/v1/instrumental/query/{task_id}` | Poll instrumental status |
| POST | `/v1/lyrics/generate` | Generate structured lyrics |
| POST | `/v1/lyrics/extend` | Extend existing lyrics |
| POST | `/v1/song/stem` | Separate track into stems |
| POST | `/v1/song/describe` | Analyse uploaded audio |
| POST | `/v1/files/upload` | Upload reference audio |

### Request Examples

**Song generation:**
```json
POST /v1/song/generate
{
  "lyrics": "[Verse]\nFirst verse lyrics here\n[Chorus]\nChorus lyrics here",
  "prompt": "pop, upbeat, female vocal",
  "model": "auto"
}
```

**Instrumental generation:**
```json
POST /v1/instrumental/generate
{
  "prompt": "relaxing coffee shop, acoustic guitar",
  "model": "auto"
}
```

### Response Format

**Submission response:**
```json
{
  "id": "task_abc123",
  "status": "preparing",
  "trace_id": "trace_xyz789"
}
```

**Completed song query:**
```json
{
  "id": "task_abc123",
  "status": "completed",
  "song": {
    "song_id": "song_def456",
    "title": "Song Title",
    "duration_milliseconds": 180000,
    "mp3_url": "https://cdn.mureka.ai/songs/xxx.mp3",
    "cover": "https://cdn.mureka.ai/covers/xxx.jpg",
    "lyrics": "[Verse]\nFirst verse..."
  }
}
```

## Parameters

### Song Generation

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lyrics` | string | No* | Max 3000 chars, section markers supported |
| `prompt` | string | No* | Style description, max 1000 chars |
| `model` | string | No | `auto`, `mureka-01`, `v7.5`, `v6` |

*At least one of `lyrics` or `prompt` is required.

### Instrumental Generation

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | Scene/style description, max 1000 chars |
| `model` | string | No | Default: `auto` |

### File Upload Constraints

| Purpose | Formats | Duration |
|---------|---------|----------|
| reference | mp3, m4a | 30s |
| vocal | mp3, m4a | 15-30s |
| melody | mp3, m4a, mid | 5-60s |
| instrumental | mp3, m4a | 30s |
| voice | mp3, m4a | 5-15s |

Max file size: 10 MB.

## Models

| Model | Notes |
|-------|-------|
| `auto` | System selects best model |
| `mureka-01` | Flagship, highest quality, MusiCoT technology |
| `v7.5` | Balanced quality/speed, MusiCoT |
| `v6` | Classic stable model |

## Supported Languages

Chinese (best quality), English, Japanese, Korean, Portuguese, Spanish, German, French, Italian, Russian (10 languages).

## Async Pattern

```
1. POST /v1/song/generate -> returns task_id, status: "preparing"
2. Poll GET /v1/song/query/{task_id}
   -> status: preparing -> processing -> completed | failed
3. On completed: mp3_url, cover, lyrics, duration available
```

- Average generation time: ~45 seconds
- Each generation produces 2 songs
- No webhook/callback mechanism (polling only)
- Lyrics generation is synchronous (immediate response)

## Task Status Values

| Status | Description |
|--------|-------------|
| `preparing` | Task queued |
| `processing` | Generation in progress |
| `completed` | Results available |
| `failed` | Generation failed |

## Pricing

### API Platform Plans

| Plan | Price | Concurrency |
|------|-------|-------------|
| Basic | From $30 | 5 |
| Standard | $1,000/month | 5 |
| Enterprise | $5,000+/month | 10+ |

- ~$0.03/song (standard tier)
- ~$0.12-$0.15/minute of audio
- Credits valid 12 months, non-refundable
- Website membership credits are NOT linked to API

## Rate Limits & Error Codes

| HTTP Code | Meaning |
|-----------|---------|
| 401 | Invalid API key |
| 402 | Insufficient credits |
| 429 | Rate limit / concurrency cap exceeded |
| 500 | Server error |

Concurrency limits: 5 (Basic/Standard), 10+ (Enterprise).

## Output Formats

- MP3 (primary, direct `mp3_url` in response)
- WAV (available for export)
- MP4 (video format)
- Stems (individual tracks via `/v1/song/stem`)

## SDK & Client Libraries

No official pip/npm package. Available tooling:

1. **REST API** -- direct HTTP calls (what this project uses)
2. **MCP Server** -- `uvx mureka-mcp` ([SkyworkAI/Mureka-mcp](https://github.com/SkyworkAI/Mureka-mcp))
3. **This project's client** -- `backend/src/infrastructure/adapters/mureka/client.py` (async httpx)

## Existing Integration in voice-lab

```
backend/src/
  infrastructure/adapters/mureka/client.py    # MurekaAPIClient (async httpx)
  domain/entities/music.py                     # MusicGenerationJob entity
  domain/services/music/service.py             # MusicGenerationService
  domain/repositories/music_job_repository.py  # IMusicGenerationJobRepository
  presentation/api/routes/music.py             # FastAPI endpoints
  presentation/api/schemas/music_schemas.py    # Pydantic schemas
  config.py                                    # mureka_api_key, mureka_api_base_url
```

## Sources

- [Mureka API Documentation](https://platform.mureka.ai/docs/)
- [Mureka API FAQ](https://platform.mureka.ai/docs/en/faq.html)
- [Mureka Quickstart](https://platform.mureka.ai/docs/en/quickstart.html)
- [Mureka Changelog](https://platform.mureka.ai/docs/en/changelog.html)
- [SkyworkAI/Mureka-mcp (GitHub)](https://github.com/SkyworkAI/Mureka-mcp)
- [Mureka O1 Announcement (Oct 2025)](https://www.globenewswire.com/news-release/2025/10/14/3165896/0/en/)
