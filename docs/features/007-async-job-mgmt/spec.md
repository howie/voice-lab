# Feature Spec: Async Job Management

**Status**: Draft
**Priority**: P2
**Created**: 2026-01-20

---

## Problem Statement

目前 Multi-Role TTS 合成是同步請求-回應模式：
- 使用者按下「產生語音」後必須等待完成
- 如果離開頁面，請求會被取消，工作會丟失
- 沒有 Job 狀態追蹤，無法查詢進度或歷史

### 現有問題

1. **使用者體驗差**：長時間合成（多角色、長對話）需要等待
2. **工作易丟失**：網路斷線或頁面離開導致工作丟失
3. **無法追蹤**：沒有歷史記錄，無法重新下載之前的結果
4. **資源浪費**：TTS Provider 可能已完成但結果無法取得

---

## Goals

1. 支援 TTS 合成工作在背景執行
2. 使用者可離開頁面，稍後回來查看結果
3. 提供 Job 狀態追蹤（pending/processing/completed/failed）
4. 保留歷史記錄供下載和重播

---

## User Stories

### US1: 背景合成 (P1)
**As a** 使用者
**I want to** 啟動 TTS 合成後可以離開頁面
**So that** 我不需要等待長時間的合成完成

**Acceptance Criteria:**
- [ ] 點擊「產生語音」後顯示 Job ID
- [ ] 可以離開頁面，Job 繼續在背景執行
- [ ] 完成後可透過通知或列表查看結果

### US2: 工作狀態追蹤 (P1)
**As a** 使用者
**I want to** 查看我的 TTS 工作狀態
**So that** 我知道合成進度和預計完成時間

**Acceptance Criteria:**
- [ ] 顯示 Job 列表（最近 N 筆）
- [ ] 每個 Job 顯示狀態：pending / processing / completed / failed
- [ ] 顯示建立時間、完成時間、耗時
- [ ] Failed 的 Job 顯示錯誤原因

### US3: 歷史記錄與下載 (P2)
**As a** 使用者
**I want to** 查看和下載之前完成的 TTS 結果
**So that** 我不需要重新合成相同的內容

**Acceptance Criteria:**
- [ ] 列出最近 30 天的完成記錄
- [ ] 可重新播放和下載音檔
- [ ] 顯示原始參數（provider、對話內容、語音設定）

---

## Technical Design (Draft)

### Database Schema

```sql
CREATE TABLE tts_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),

    -- Job metadata
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending/processing/completed/failed
    job_type VARCHAR(50) NOT NULL,  -- 'multi_role_tts', 'single_tts'

    -- Input
    provider VARCHAR(50) NOT NULL,
    input_json JSONB NOT NULL,  -- Stores turns, voice_assignments, etc.

    -- Output
    audio_file_id UUID REFERENCES audio_files(id),
    result_json JSONB,  -- duration_ms, latency_ms, turn_timings, etc.
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Indexes
    INDEX idx_tts_jobs_user_status (user_id, status),
    INDEX idx_tts_jobs_created (created_at DESC)
);
```

### Architecture Options

#### Option A: Celery + Redis
- **Pros**: 成熟穩定、支援重試、監控工具完善
- **Cons**: 需要額外的 Redis 和 Celery worker 部署

#### Option B: PostgreSQL-based Queue (pg-boss / SKIP LOCKED)
- **Pros**: 不需額外服務、與現有 DB 整合
- **Cons**: 效能較低、功能較少

#### Option C: FastAPI BackgroundTasks + DB Polling
- **Pros**: 最簡單、不需額外服務
- **Cons**: 不支援持久化、重啟會丟失工作

**建議**: Option A (Celery + Redis) for production readiness

### API Endpoints (Draft)

```
POST   /api/v1/jobs/tts/multi-role     # Create async job
GET    /api/v1/jobs/{job_id}           # Get job status
GET    /api/v1/jobs                    # List user's jobs
DELETE /api/v1/jobs/{job_id}           # Cancel job (if pending)
GET    /api/v1/jobs/{job_id}/download  # Download completed audio
```

### Frontend Changes

1. **Job 提交後**：顯示 Job ID，提供「查看進度」連結
2. **新增 Jobs 頁面**：列出所有工作及狀態
3. **通知機制**：WebSocket 或 Polling 更新狀態
4. **結果頁面**：播放、下載、查看參數

---

## Out of Scope

- Job 優先級排序
- 批次提交多個 Jobs
- Job 重試策略配置（使用預設）
- 多租戶隔離（目前單一用戶環境）

---

## Open Questions

1. Job 保留多久？（建議：30 天）
2. 音檔儲存位置？（建議：S3 or local storage）
3. 同時執行的 Job 上限？（建議：每用戶 3 個）
4. 是否需要 WebSocket 即時通知？（建議：先用 polling）

---

## References

- [Celery Documentation](https://docs.celeryq.dev/)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- Current implementation: `docs/features/005-multi-role-tts/`
