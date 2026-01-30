# Suno AI vs Mureka: Feature Comparison

## API Availability

| Aspect | Mureka | Suno |
|--------|--------|------|
| Official public API | Yes (`api.mureka.ai`) | **No** |
| API documentation | Official docs at `platform.mureka.ai/docs` | None (unofficial community docs) |
| Authentication | Bearer Token (API key) | Cookie-based scraping or third-party API keys |
| API stability | Versioned, stable (`/v1/`) | Reverse-engineered, can break anytime |
| TOS compliance | Full compliance | **High risk** -- scraping likely violates TOS |
| Commercial licensing | Clear, royalty-free for API users | Ambiguous for unofficial API usage |
| SLA / Support | Yes (`api-support@mureka.ai`, 24h response) | None |

## Core Capabilities

| Feature | Mureka | Suno |
|---------|--------|------|
| Song generation (vocals) | `POST /v1/song/generate` | `POST /api/custom_generate` (unofficial) |
| Instrumental / BGM | `POST /v1/instrumental/generate` | `make_instrumental: true` param |
| Lyrics generation | `POST /v1/lyrics/generate` | `POST /api/generate_lyrics` (unofficial) |
| Lyrics extension | `POST /v1/lyrics/extend` | N/A |
| Song extension | N/A (lyrics extend only) | `POST /api/extend_audio` (continue from timestamp) |
| Song concatenation | N/A | `POST /api/concat` (unofficial) |
| Stem separation | `POST /v1/song/stem` | `POST /api/generate_stems` (unofficial) |
| Song analysis/describe | `POST /v1/song/describe` | N/A |
| File upload (reference audio) | `POST /v1/files/upload` | N/A |

## Generation Parameters

| Parameter | Mureka | Suno |
|-----------|--------|------|
| Lyrics input | Max 3000 chars, section markers | Max 500 chars (simple), full lyrics (custom) |
| Style/prompt | Max 1000 chars | Max 200 chars (v4), 1000 chars (v4.5+) |
| Title | N/A (auto-generated) | User-specified in custom mode |
| Model selection | `auto`, `mureka-01`, `v7.5`, `v6` | `chirp-crow` (v5), `chirp-bluejay`, `chirp-auk`, `chirp-v4` |
| Instrumental flag | Separate endpoint | `make_instrumental: boolean` |
| Wait for result | Polling-based | `wait_audio: boolean` or polling |
| Results per request | 2 songs | 2 clips |

## Audio Output

| Aspect | Mureka | Suno |
|--------|--------|------|
| Max duration | ~5 minutes | ~8 minutes (v4.5+) |
| Output formats | MP3, WAV, MP4 | MP3 (all), WAV (paid subscribers only) |
| Stem output | Yes (vocals, drums, bass, etc.) | Yes (unofficial) |
| CDN delivery | `cdn.mureka.ai` | `cdn1.suno.ai` |

## Async & Job Management

| Aspect | Mureka | Suno |
|--------|--------|------|
| Submission pattern | POST returns `task_id` | POST returns `clip_id`(s) |
| Status polling | `GET /v1/song/query/{task_id}` | `GET /api/get?ids=clip_id1,clip_id2` |
| Status values | preparing, processing, completed, failed | submitted, queued, streaming, complete |
| Webhook/callback | **No** | Third-party proxy services only |
| Average gen time | ~45 seconds | ~30-90 seconds |
| Lyrics generation | Synchronous (immediate) | Synchronous (immediate) |

## Models

### Mureka Models

| Model | Notes |
|-------|-------|
| `auto` | System selects best model |
| `mureka-01` | Flagship, highest quality, MusiCoT technology |
| `v7.5` | Balanced quality/speed, MusiCoT |
| `v6` | Classic stable model |

### Suno Models

| Model | Version | Max Duration | Notes |
|-------|---------|-------------|-------|
| `chirp-crow` | v5 | TBD | Latest, studio-grade, ELO 1293 |
| `chirp-bluejay` | v4.5+ | 8 min | Enhanced prompts |
| `chirp-auk` | v4.5 | 8 min | Faster generation |
| `chirp-v4` | v4 | 4 min | Good vocal quality |
| `chirp-v3-5` | v3.5 | 4 min | Deprecated Sept 2025 |

## Languages

| Provider | Supported Languages |
|----------|-------------------|
| Mureka | Chinese (best), English, Japanese, Korean, Portuguese, Spanish, German, French, Italian, Russian (10 languages) |
| Suno | Multi-language (exact list unspecified), reportedly 50+ languages via v5 |

## Pricing

### Platform/Subscription

| Plan | Mureka | Suno |
|------|--------|------|
| Free | Limited trial credits | 50 credits/day |
| Pro | $10/month (500 songs) | ~$8/month (2,500 credits) |
| Premier | $30/month (2,000 songs) | ~$24/month (10,000 credits) |

### API Pricing

| Aspect | Mureka | Suno (third-party) |
|--------|--------|-------------------|
| Per-song cost | ~$0.03 | ~$0.01-$0.04 |
| Concurrency | 5-10 (plan-dependent) | 2-5 (account-dependent) |
| Enterprise | $5,000+/month, custom | N/A |

## SDK & Client Libraries

| Aspect | Mureka | Suno |
|--------|--------|------|
| Official SDK | None (REST API + MCP server) | **None** |
| Official MCP | Yes (`uvx mureka-mcp`) | No |
| Unofficial Python | N/A | `SunoAI` (pip), `suno-api` (pip) |
| Unofficial Node.js | N/A | `gcui-art/suno-api` (GitHub) |
| This project's client | `backend/src/infrastructure/adapters/mureka/client.py` | N/A |

## Risk Assessment

| Risk | Mureka | Suno |
|------|--------|------|
| API breaking changes | Low (versioned) | **High** (reverse-engineered) |
| Service discontinuation | Low (backed by Kunlun Tech) | High for unofficial access |
| Legal/TOS risk | None | **High** (cookie scraping) |
| Auth token expiry | API keys don't expire | Cookies expire, need manual refresh |
| CAPTCHA challenges | None | **Required** (2Captcha or similar) |
| Rate limiting | Clear limits, HTTP 429 | Undocumented, unpredictable |
