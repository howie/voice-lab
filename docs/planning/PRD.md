# Voice Lab - Product Requirement Document (PRD)

**Version**: 1.0
**Created**: 2026-01-16
**Status**: Draft

---

## 1. Executive Summary

Voice Lab 是一個內部測試平台，讓公司非技術人員能夠輕鬆測試和比較市面上主要語音服務提供商的功能。平台支援文字轉語音 (TTS)、語音轉文字 (STT) 及即時語音互動 (Interaction) 三大核心功能，協助團隊選擇最適合產品需求的語音技術方案。

---

## 2. Problem Statement

### 2.1 Current Pain Points

1. **評估語音服務困難**：目前評估不同語音提供商需要工程師撰寫測試程式，流程繁瑣
2. **缺乏標準化比較**：各家 Provider 的測試結果散落各處，難以系統性比較
3. **非技術人員參與困難**：產品經理、設計師無法直接測試語音品質，需依賴工程師
4. **中文兒童語音辨識**：特殊場景（如中文小孩講話）的辨識效果缺乏系統性測試

### 2.2 Target Users

| 角色 | 需求 | 使用頻率 |
|------|------|----------|
| 產品經理 | 評估各家語音品質、選擇適合的 Provider | 每週數次 |
| 設計師 | 測試不同音色、調整語音參數 | 專案期間密集 |
| 內容編輯 | 產生故事音檔、測試敘事效果 | 每日 |
| 工程師 | 整合測試、除錯、API 驗證 | 開發期間 |

---

## 3. Product Vision

> 打造一個簡單直覺的語音實驗平台，讓團隊成員無需撰寫程式碼，即可快速測試、比較各家語音服務，加速產品決策。

---

## 4. Supported Voice Providers

| Provider | TTS | STT | Interaction | 備註 |
|----------|-----|-----|-------------|------|
| **Google Cloud Platform (GCP)** | ✅ | ✅ | ✅ | Cloud Speech-to-Text, Cloud Text-to-Speech, Dialogflow |
| **Microsoft Azure** | ✅ | ✅ | ✅ | Azure Speech Services, Azure OpenAI |
| **ElevenLabs** | ✅ | ❌ | ❌ | 專注高品質 TTS，支援 Voice Cloning |
| **VoAI** | ✅ | ✅ | ✅ | 台灣本土供應商，中文支援度高 |

---

## 5. Feature Requirements

### 5.1 Module 1: TTS (Text-to-Speech) 測試平台

讓使用者輸入文字，透過不同 Provider 產生語音，比較各家音質和特色。

#### Functional Requirements

| ID | 需求描述 | Priority |
|----|----------|----------|
| TTS-001 | 使用者可輸入任意文字內容（支援中文、英文、混合） | P0 |
| TTS-002 | 使用者可選擇 Provider（GCP, Azure, ElevenLabs, VoAI） | P0 |
| TTS-003 | 使用者可選擇語音角色（Voice ID / Voice Name） | P0 |
| TTS-004 | 使用者可調整語速（0.5x - 2.0x） | P1 |
| TTS-005 | 使用者可調整音調（pitch: -20 ~ +20 半音） | P1 |
| TTS-006 | 使用者可調整音量（volume: 0% - 200%） | P1 |
| TTS-007 | 系統顯示每個 Provider 支援的參數選項 | P1 |
| TTS-008 | 使用者可同時產生多家 Provider 的語音進行 A/B 比較 | P0 |
| TTS-009 | 使用者可試聽產生的語音 | P0 |
| TTS-010 | 使用者可下載產生的音檔（支援 mp3, wav, opus） | P0 |
| TTS-011 | 系統紀錄產生的歷史紀錄（含參數設定） | P1 |
| TTS-012 | 系統顯示 API 回應時間與成本估算 | P2 |

#### User Stories

**US-TTS-01**: 作為產品經理，我想要輸入一段故事文字，選擇不同的語音角色，比較各家 TTS 的語音品質，以便決定採用哪家服務。

**US-TTS-02**: 作為內容編輯，我想要調整語速和音調，產生不同風格的故事音檔，以便找出最適合目標受眾的設定。

**US-TTS-03**: 作為設計師，我想要快速 A/B 比較 ElevenLabs 和 Azure 的女聲，以便選擇最自然的音色。

---

### 5.2 Module 2: STT (Speech-to-Text) 測試平台

測試各家語音辨識的準確度，特別針對中文兒童語音場景。

#### Functional Requirements

| ID | 需求描述 | Priority |
|----|----------|----------|
| STT-001 | 使用者可透過麥克風即時錄音 | P0 |
| STT-002 | 使用者可上傳音檔進行辨識（支援 mp3, wav, m4a, webm） | P0 |
| STT-003 | 使用者可選擇 Provider（GCP, Azure, VoAI） | P0 |
| STT-004 | 使用者可選擇辨識語言（zh-TW, zh-CN, en-US, ja-JP） | P0 |
| STT-005 | 系統顯示辨識結果（含逐字稿） | P0 |
| STT-006 | 系統顯示辨識信心分數（confidence score） | P1 |
| STT-007 | 使用者可同時送出多家 Provider 進行比較 | P0 |
| STT-008 | 系統支援串流辨識（即時顯示辨識過程） | P1 |
| STT-009 | 使用者可標記「正確答案」計算 WER (Word Error Rate) | P1 |
| STT-010 | 系統紀錄測試歷史（含音檔、辨識結果、正確率） | P1 |
| STT-011 | 系統顯示 API 回應時間 | P2 |
| STT-012 | 使用者可選擇「兒童語音模式」最佳化辨識 | P1 |

#### User Stories

**US-STT-01**: 作為產品經理，我想要上傳小朋友的錄音檔，測試各家 STT 對兒童中文的辨識率，以便評估適合度。

**US-STT-02**: 作為工程師，我想要即時錄音並看到串流辨識結果，以便驗證 API 整合是否正常。

**US-STT-03**: 作為內容編輯，我想要建立測試語料庫，批次測試各家辨識準確度，以便產生比較報告。

---

### 5.3 Module 3: Interaction 即時互動測試平台

測試各家即時語音對話的效果，包含回應速度、理解正確率、語音自然度。

#### Functional Requirements

| ID | 需求描述 | Priority |
|----|----------|----------|
| INT-001 | 使用者可發起即時語音對話 | P0 |
| INT-002 | 使用者可選擇 Provider 組合（STT + LLM + TTS） | P0 |
| INT-003 | 系統支援語音輸入 → AI 理解 → 語音回覆 完整流程 | P0 |
| INT-004 | 系統顯示端到端延遲（End-to-End Latency） | P0 |
| INT-005 | 系統分別顯示 STT、LLM、TTS 各階段延遲 | P1 |
| INT-006 | 使用者可設定對話情境（System Prompt） | P1 |
| INT-007 | 系統支援打斷（Barge-in）功能測試 | P2 |
| INT-008 | 系統紀錄對話歷史（含音檔、文字、時間戳） | P1 |
| INT-009 | 使用者可評分每次對話體驗（1-5 星） | P2 |
| INT-010 | 系統支援預設情境模板（如：故事互動、問答） | P2 |

#### User Stories

**US-INT-01**: 作為產品經理，我想要測試完整的語音互動流程，量測從說話到 AI 回覆的總延遲，以便評估用戶體驗。

**US-INT-02**: 作為設計師，我想要嘗試不同的 Provider 組合（如 GCP STT + Claude + ElevenLabs TTS），找出延遲與品質的最佳平衡。

**US-INT-03**: 作為工程師，我想要測試打斷功能的表現，確保使用者中途說話時系統能正確處理。

---

### 5.4 Module 4: Advanced Features (進階功能)

#### 5.4.1 後製工具

| ID | 需求描述 | Priority |
|----|----------|----------|
| ADV-001 | 使用者可對產生的音檔進行混音（加入背景音樂） | P2 |
| ADV-002 | 使用者可調整音檔的 EQ（均衡器） | P3 |
| ADV-003 | 使用者可串接多段音檔 | P2 |
| ADV-004 | 使用者可加入音效（轉場、特效） | P3 |
| ADV-005 | 使用者可匯出最終混音成品 | P2 |

#### 5.4.2 批次處理

| ID | 需求描述 | Priority |
|----|----------|----------|
| ADV-006 | 使用者可上傳 CSV/Excel 批次產生多段 TTS | P2 |
| ADV-007 | 使用者可建立語料庫批次測試 STT | P2 |
| ADV-008 | 系統自動產生比較報表（Excel/PDF） | P2 |

---

## 6. Non-Functional Requirements

### 6.1 Performance

| ID | 需求描述 | 目標值 |
|----|----------|--------|
| NFR-001 | TTS 產生時間 | < 3 秒（100 字內） |
| NFR-002 | STT 辨識延遲 | < 2 秒（5 秒音檔） |
| NFR-003 | 頁面載入時間 | < 2 秒 |
| NFR-004 | 同時支援使用者數 | ≥ 20 人 |

### 6.2 Usability

| ID | 需求描述 |
|----|----------|
| NFR-005 | 非技術人員無需訓練即可上手基本功能 |
| NFR-006 | 支援 Desktop 瀏覽器（Chrome, Safari, Edge） |
| NFR-007 | 提供中文操作介面 |

### 6.3 Security

| ID | 需求描述 |
|----|----------|
| NFR-008 | Provider API Key 不得暴露至前端 |
| NFR-009 | 使用者需登入才能使用（公司內部帳號） |
| NFR-010 | 測試紀錄僅限內部存取 |

### 6.4 Maintainability

| ID | 需求描述 |
|----|----------|
| NFR-011 | 新增 Provider 只需實作統一介面，不需修改核心邏輯 |
| NFR-012 | 支援 Provider 設定熱更新（不需重新部署） |

---

## 7. Success Metrics

| Metric | 目標 | 量測方式 |
|--------|------|----------|
| 月活躍用戶 (MAU) | ≥ 10 人 | 系統登入紀錄 |
| TTS 測試次數 | ≥ 500 次/月 | API 呼叫紀錄 |
| 使用者滿意度 | ≥ 4/5 分 | 問卷調查 |
| Provider 評估報告產出 | ≥ 2 份/季 | 文件追蹤 |

---

## 8. Out of Scope (MVP)

以下功能不在 MVP 範圍內，可作為後續迭代考量：

- Voice Cloning（語音複製）
- Custom Voice Training（自訂語音訓練）
- 多語言自動偵測
- Mobile App
- 公開 API 供外部使用
- 計費管理系統

---

## 9. Dependencies & Assumptions

### Dependencies

1. 各 Provider 的 API Key 已取得並設定
2. 公司內部 SSO/身份驗證系統可整合
3. 雲端儲存服務可用於儲存測試音檔

### Assumptions

1. 使用者具備基本的語音測試知識（知道 TTS、STT 的概念）
2. 測試主要在辦公室網路環境進行
3. 產生的音檔僅供內部測試使用，不對外發布

---

## 10. Appendix

### A. Voice Provider Comparison Matrix

| Feature | GCP | Azure | ElevenLabs | VoAI |
|---------|-----|-------|------------|------|
| 中文 TTS 品質 | ★★★★☆ | ★★★★★ | ★★★★☆ | ★★★★☆ |
| 英文 TTS 品質 | ★★★★☆ | ★★★★☆ | ★★★★★ | ★★★☆☆ |
| 中文 STT 準確度 | ★★★★☆ | ★★★★☆ | N/A | ★★★★★ |
| 兒童語音辨識 | ★★★☆☆ | ★★★☆☆ | N/A | ★★★★☆ |
| 定價 | 中等 | 中等 | 較高 | 低 |
| 延遲 | 低 | 低 | 中等 | 低 |

*註：以上評分為初步估計，需透過 Voice Lab 實際測試驗證*

### B. Glossary

| 術語 | 說明 |
|------|------|
| TTS | Text-to-Speech，文字轉語音 |
| STT | Speech-to-Text，語音轉文字 |
| WER | Word Error Rate，字錯誤率 |
| Barge-in | 打斷功能，使用者在 AI 說話時可中斷 |
| Latency | 延遲，從輸入到輸出的時間 |
| Voice ID | 語音角色識別碼 |
