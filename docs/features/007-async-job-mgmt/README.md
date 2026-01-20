# 007: Async Job Management

**Status**: 📝 Draft (Not Started)
**Priority**: P2
**Prerequisite**: 005-multi-role-tts

## Summary

將 TTS 合成從同步請求改為背景工作處理，支援：
- 背景執行長時間合成任務
- 工作狀態追蹤 (pending/processing/completed/failed)
- 歷史記錄查詢與下載

## Motivation

目前問題：
1. 使用者離開頁面會導致合成工作丟失
2. 沒有工作狀態追蹤
3. 無法查詢歷史或重新下載

## Documents

| Document | Status | Description |
|----------|--------|-------------|
| [spec.md](./spec.md) | ✅ Draft | 功能規格書 |
| plan.md | ❌ | 實作計畫 |
| tasks.md | ❌ | 工作清單 |

## Key Decisions (TBD)

- [ ] 工作佇列技術選型 (Celery vs pg-boss vs BackgroundTasks)
- [ ] 音檔儲存方案 (S3 vs Local)
- [ ] 前端通知機制 (WebSocket vs Polling)
