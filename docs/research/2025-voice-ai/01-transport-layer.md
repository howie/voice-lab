# 傳輸層技術研究

> 最後更新：2025-01

## 概述

傳輸層負責在客戶端與伺服器之間傳輸即時音訊/視訊串流。低延遲和穩定性是關鍵。

## 技術比較

### WebRTC (現行標準)

**狀態**: ✅ 生產就緒

| 項目 | 說明 |
|------|------|
| 延遲 | < 100ms (理想條件) |
| 瀏覽器支援 | 所有主流瀏覽器 |
| 協議 | UDP-based (SRTP) |

**優點**:
- 成熟穩定，廣泛部署
- 內建 NAT 穿透 (ICE/STUN/TURN)
- P2P 和 SFU 架構支援
- 豐富的 codec 支援 (Opus, VP8/VP9, H.264)

**缺點**:
- 設定複雜 (STUN/TURN 伺服器)
- 大規模部署需要 SFU
- 不支援原生廣播

**主要實作**:
| 名稱 | 語言 | 說明 |
|------|------|------|
| [libwebrtc](https://webrtc.googlesource.com/src/) | C++ | Google 官方實作 |
| [Pion](https://github.com/pion/webrtc) | Go | 純 Go 實作 |
| [aiortc](https://github.com/aiortc/aiortc) | Python | asyncio 實作 |
| [mediasoup](https://mediasoup.org/) | Node.js/C++ | SFU 伺服器 |

---

### MoQ (Media over QUIC) - 未來趨勢

**狀態**: 🔬 實驗階段 (IETF Draft)

| 項目 | 說明 |
|------|------|
| 延遲 | 目標 < 100ms |
| 標準化 | IETF 進行中 |
| 協議 | QUIC-based |

**優點**:
- 基於 QUIC，內建加密和多路復用
- 支援廣播和大規模分發
- 更好的擁塞控制
- 統一的媒體傳輸協議

**缺點**:
- 標準尚未定稿
- 瀏覽器支援有限
- 生態系統不成熟
- 實作經驗不足

**相關資源**:
- [IETF MoQ WG](https://datatracker.ietf.org/wg/moq/about/)
- [MoQ Spec Draft](https://datatracker.ietf.org/doc/draft-ietf-moq-transport/)

---

## 選型建議

```
                    ┌─────────────────┐
                    │ 需要即時雙向通訊？ │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
          是 (對話)                     否 (播放)
              │                             │
              ▼                             ▼
         ┌────────┐                   ┌──────────┐
         │ WebRTC │                   │ HLS/DASH │
         └────────┘                   └──────────┘
```

### 2025 年建議

| 場景 | 推薦 | 理由 |
|------|------|------|
| Voice AI 對話 | WebRTC | 成熟穩定，低延遲 |
| 大規模廣播 | 持續觀望 MoQ | 等待標準定稿 |
| 混合場景 | WebRTC + CDN | 彈性架構 |

## 實作注意事項

### WebRTC 部署清單

- [ ] STUN 伺服器設定
- [ ] TURN 伺服器 (防火牆穿透)
- [ ] SFU 選擇 (LiveKit, mediasoup)
- [ ] Codec 設定 (推薦 Opus for audio)
- [ ] 網路品質監控

### 延遲優化

1. **Jitter Buffer**: 調整至最小可接受值
2. **Codec**: 使用 Opus 48kHz
3. **位置**: 選擇靠近用戶的節點
4. **TURN**: 確保有足夠的 relay 容量

## 參考連結

- [WebRTC.org](https://webrtc.org/)
- [WebRTC Samples](https://webrtc.github.io/samples/)
- [High Performance Browser Networking - WebRTC](https://hpbn.co/webrtc/)

## 更新日誌

| 日期 | 變更 |
|------|------|
| 2025-01 | 初始版本 |
