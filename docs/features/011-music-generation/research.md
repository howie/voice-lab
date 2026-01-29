# Research: Music Generation Integration

**研究日期**: 2026-01-29
**研究主題**: 整合 Mureka AI 平台進行音樂和音效生成

---

## 研究目標

評估 Mureka AI 作為 Voice Lab 音樂生成功能的整合選項，了解其 API 能力、限制和成本結構。

---

## Mureka AI 平台概述

### 公司背景

- **開發商**: 昆侖科技（Kunlun Tech）
- **核心技術**: SkyMusic 2.0 模型
- **定位**: AI 音樂生成領域首個官方 API 平台提供商
- **特點**: 提供直接技術支援，服務安全合規

### 主要功能

| 功能 | 說明 |
|------|------|
| **歌曲生成** | 根據歌詞、風格描述生成完整歌曲（含人聲） |
| **純音樂生成** | 根據場景描述生成背景音樂/配樂 |
| **歌詞生成** | 根據主題生成結構化歌詞 |
| **歌曲延伸** | 延伸現有歌曲內容 |

### 技術規格

- **最大歌曲長度**: 5 分鐘
- **支援語言**: 10 種語言（中文品質最佳）
- **輸出格式**: MP3, WAV, Stems (Pro tier)
- **並發限制**: 每帳戶最多 10 個並發生成
- **平均生成時間**: 約 45 秒
- **每次生成產出**: 2 首歌曲選項

---

## API 架構分析

### 認證方式

- **類型**: Bearer Token (HTTP Bearer)
- **取得方式**: [platform.mureka.ai/apiKeys](https://platform.mureka.ai/apiKeys)

### API Endpoints

| 端點 | 方法 | 用途 |
|------|------|------|
| `/v1/song/generate` | POST | 提交歌曲生成任務 |
| `/v1/song/query/{task_id}` | GET | 查詢歌曲任務狀態 |
| `/v1/instrumental/generate` | POST | 提交純音樂生成任務 |
| `/v1/instrumental/query/{task_id}` | GET | 查詢純音樂任務狀態 |
| `/v1/lyrics/generate` | POST | 生成歌詞 |
| `/v1/lyrics/extend` | POST | 延伸歌詞 |

### 非同步任務流程

```
1. POST /v1/song/generate → 返回 task_id
2. 輪詢 GET /v1/song/query/{task_id}
3. 狀態: preparing → processing → completed/failed
4. completed 時返回 mp3_url、cover、lyrics 等
```

### 任務狀態

| 狀態 | 說明 |
|------|------|
| `preparing` | 任務初始化 |
| `processing` | AI 生成中 |
| `completed` | 完成，可取得結果 |
| `failed` | 失敗 |

---

## 模型選項

| 模型 | 說明 | 推薦場景 |
|------|------|----------|
| `auto` | 自動選擇最適合模型 | 一般使用 |
| `mureka-01` | 最新旗艦模型 (O1) | 高品質要求 |
| `v7.5` | 平衡型模型 | 一般使用 |
| `v6` | 經典穩定模型 | 相容性需求 |

---

## 定價結構

### Web 方案（適用於試用和小量使用）

| 方案 | 月費 | 配額 | 單價 |
|------|------|------|------|
| Free | $0 | 有限試用 | - |
| Pro | $10 | 500 歌曲 | $0.02/首 |
| Premier | $30 | 2,000 歌曲 | $0.015/首 |

### API 方案（適用於系統整合）

| 方案 | 價格 | 並發數 | 備註 |
|------|------|--------|------|
| 基礎 | $30 起 | 5 | Pay-as-you-go |
| 標準 | $1,000/月 | 5 | $0.03/首 |
| 企業 | $5,000+ | 10+ | 大量使用 |

### 配額規則

- 額度有效期: 12 個月（從充值日起算）
- 消費順序: FIFO（先付費後贈送）
- 退款政策: 不支援退款

---

## 商業授權

**付費 API 生成的內容享有**:
- 完整使用權
- 商業授權
- 免版稅 (Royalty-Free)
- 可用於：商業產品、平台發布、廣告、影片等

---

## 整合選項

### 選項 1: 直接 REST API 整合

**優點**:
- 完全控制 API 呼叫邏輯
- 可自訂重試和錯誤處理
- 無額外依賴

**缺點**:
- 需自行實作輪詢邏輯
- 需處理認證和錯誤

**適用場景**: 生產環境整合

### 選項 2: MCP Server 整合

**優點**:
- 官方維護
- 與 Claude Desktop 等 MCP 客戶端整合

**缺點**:
- 需要 MCP 運行環境
- 較少客製化彈性

**適用場景**: 快速原型、Claude 整合場景

### 建議

對於 Voice Lab，建議採用 **選項 1: 直接 REST API 整合**：
- 與現有 Backend 架構一致
- 可整合 007-async-job-mgmt 機制
- 保持技術棧統一

---

## 競品比較

| 特性 | Mureka AI | Suno AI | Udio |
|------|-----------|---------|------|
| 官方 API | ✅ | ❌ | ❌ |
| 中文支援 | ✅ 優秀 | ✅ | ✅ |
| 歌詞生成 | ✅ | ✅ | ✅ |
| 純音樂生成 | ✅ | ✅ | ✅ |
| 商業授權 | ✅ 明確 | ⚠️ 限制 | ⚠️ 限制 |
| API 定價 | 透明 | N/A | N/A |

**結論**: Mureka AI 是目前唯一提供官方 API 且商業授權明確的選項。

---

## 風險評估

| 風險 | 機率 | 影響 | 緩解措施 |
|------|------|------|----------|
| API 服務中斷 | 低 | 高 | 實作重試機制、錯誤處理 |
| API 變更 | 中 | 中 | 封裝 API 呼叫、版本控制 |
| 配額超額 | 中 | 中 | 用量監控、設定上限 |
| 生成品質不穩定 | 中 | 中 | 提供重新生成功能 |
| 費用超支 | 低 | 中 | 設定預算警示 |

---

## 實作建議

### Phase 1: MVP

1. 實作純音樂（BGM）生成功能
2. 整合 007-async-job-mgmt
3. 基本的狀態查詢和下載

### Phase 2: 完整功能

1. 加入歌曲生成（含人聲）
2. 加入歌詞生成
3. 歷史記錄管理
4. 配額追蹤

### Phase 3: 進階功能

1. 模型選擇 UI
2. 風格模板
3. 與 Magic DJ 深度整合

---

## 參考資料

- [Mureka API Platform](https://platform.mureka.ai/)
- [Mureka API Documentation](https://platform.mureka.ai/docs/)
- [Mureka MCP Server](https://github.com/SkyworkAI/Mureka-mcp)
- [Mureka AI 官網](https://www.mureka.ai/)
- [Mureka 定價](https://platform.mureka.ai/pricing)
- [Mureka FAQ](https://platform.mureka.ai/docs/en/faq.html)

---

*Last updated: 2026-01-29*
