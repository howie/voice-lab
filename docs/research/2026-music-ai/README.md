# Music AI API Research

> Last Updated: 2026-02-19

## Purpose

Research and compare music generation APIs for integration into voice-lab, evaluating capabilities, pricing, and feasibility.

## Documents

| File | Description |
|------|-------------|
| [comparison.md](./comparison.md) | Suno vs Mureka side-by-side feature comparison |
| [suno-api.md](./suno-api.md) | Suno AI API detailed research |
| [mureka-api.md](./mureka-api.md) | Mureka API detailed research |
| [factory-pattern-proposal.md](./factory-pattern-proposal.md) | Factory pattern feasibility analysis and proposed architecture |
| [gemini-lyria-music.md](./gemini-lyria-music.md) | Google Gemini / Lyria 音樂生成研究 (Lyria 2, Lyria 3, Lyria RealTime) |

## TL;DR

| Aspect | Mureka | Suno |
|--------|--------|------|
| Official API | Yes | **No** (unofficial only) |
| Auth | Bearer Token (API key) | Cookie-based / third-party key |
| Production-ready | Yes | No |
| Song generation | Yes | Yes |
| Instrumental | Yes | Yes |
| Lyrics generation | Yes | Yes |
| Song extension | Yes (lyrics extend) | Yes |
| Stem separation | Yes | Yes (unofficial) |
| Max duration | ~5 min | ~8 min (v4.5+) |
| Async pattern | POST + poll task_id | POST + poll clip IDs |
| Pricing (API) | ~$0.03/song | ~$0.01-$0.04 (third-party) |

## Conclusion

1. **Mureka remains the recommended production provider** due to its official, documented API with clear licensing.
2. **Suno lacks an official API** -- all integrations rely on reverse-engineered endpoints or third-party proxies, which carry TOS and stability risks.
3. **A factory pattern is feasible** and aligns with the existing TTS provider pattern in the codebase. The two services share enough common surface area (song generation, instrumental, lyrics) to be abstracted behind `IMusicProvider`.
4. **Recommendation**: Build the `IMusicProvider` interface and `MusicProviderFactory` now using Mureka as the first concrete implementation. Add Suno support later if/when an official API becomes available.
