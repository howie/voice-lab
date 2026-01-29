# Speckit Skill 與 Claude Code Cloud 整合計畫

> 版本: 1.0.0 | 日期: 2026-01-29

## 概述

根據 [Claude Code Cloud 官方文件](https://code.claude.com/docs/en/claude-code-on-the-web)，Cloud 環境**完全支援** Bash 腳本和 Git 操作，因此現有的 speckit skill 只需少量調整即可在 Cloud 上運作。

## 目錄

- [關鍵發現](#關鍵發現)
- [整合方案](#整合方案)
- [實作細節](#實作細節)
- [工作流程](#工作流程)
- [修改檔案清單](#修改檔案清單)
- [驗證方式](#驗證方式)
- [風險與緩解](#風險與緩解)

---

## 關鍵發現

### Cloud 環境能力（完整支援）

| 能力 | 狀態 | 說明 |
|------|------|------|
| Bash 執行 | ✅ 完整 | Claude 透過終端機和 CLI 工具操作 |
| Git 操作 | ✅ 完整 | 透過安全代理，支援 clone/fetch/push |
| 檔案系統 | ✅ 完整 | 存取授權的 repository |
| CLAUDE.md | ✅ 讀取 | Cloud 會尊重 CLAUDE.md 上下文 |
| Hooks | ✅ 支援 | SessionStart hooks 可用於初始化 |

### Cloud 環境機制

#### 啟動流程

當在 Cloud 啟動 session 時：

1. **Repository cloning** - 將你的 repo clone 到 Anthropic 管理的 VM
2. **Environment setup** - 準備安全的雲端環境
3. **Network configuration** - 配置網路存取（預設受限）
4. **Task execution** - Claude 分析程式碼、修改、執行測試
5. **Completion** - 完成後通知，可建立 PR

#### Session 傳輸

| 方向 | 方式 | 說明 |
|------|------|------|
| 本地 → Cloud | `&` 前綴或 `--remote` | 建立新的 Cloud session |
| Cloud → 本地 | `/teleport` 或 `--teleport` | 將 Cloud session 拉回本地 |

> **注意**：Session 傳輸是單向的 - 可以將 Cloud session 拉回本地，但無法將現有本地 session 推送到 Cloud。`&` 前綴會建立**新的** Cloud session。

### 需要處理的差異

1. **分支管理**：Cloud 預設 clone 預設分支，需在 prompt 中指定分支
2. **Session 傳輸**：單向（Cloud → 本地），無法推送現有本地 session
3. **平台限制**：僅支援 GitHub（不支援 GitLab）

---

## 整合方案

### 方案：最小修改

現有 skill 基本可用，只需加入 Cloud 環境偵測和提示。

#### 修改項目

1. **更新 `.claude/settings.json`** - 加入 SessionStart hook
2. **調整 skill 提示詞** - 加入 Cloud 使用說明
3. **建立狀態檔機制** - 支援跨 session 的 feature 追蹤

---

## 實作細節

### 1. SessionStart Hook

更新 `.claude/settings.json`：

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.specify/scripts/bash/cloud-init.sh"
          }
        ]
      }
    ]
  }
}
```

### 2. Cloud 初始化腳本

建立 `.specify/scripts/bash/cloud-init.sh`：

```bash
#!/bin/bash
# Cloud 環境初始化腳本
# 此腳本在 Cloud session 啟動時自動執行

set -e

# 檢查是否在 Cloud 環境
if [ "$CLAUDE_CODE_REMOTE" != "true" ]; then
  # 本地環境，無需特殊處理
  exit 0
fi

echo "🌐 Running in Claude Code Cloud environment"
echo "================================================"

# 顯示當前分支
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
echo "📌 Current branch: $CURRENT_BRANCH"

# 檢查是否有現有 feature 狀態
STATE_DIR=".specify/state"
STATE_FILE="$STATE_DIR/current-feature.json"

if [ -f "$STATE_FILE" ]; then
  echo ""
  echo "📋 Found existing feature state:"
  cat "$STATE_FILE"
  echo ""

  # 提取 feature 分支名稱
  FEATURE_BRANCH=$(jq -r '.branch // empty' "$STATE_FILE" 2>/dev/null)

  if [ -n "$FEATURE_BRANCH" ] && [ "$FEATURE_BRANCH" != "$CURRENT_BRANCH" ]; then
    echo "⚠️  Feature branch mismatch!"
    echo "   State file branch: $FEATURE_BRANCH"
    echo "   Current branch: $CURRENT_BRANCH"
    echo ""
    echo "💡 To switch to the feature branch, run:"
    echo "   git fetch && git checkout $FEATURE_BRANCH"
  fi
else
  echo "ℹ️  No existing feature state found"
  echo "   Use /speckit.specify to start a new feature"
fi

# 確保腳本可執行
echo ""
echo "🔧 Setting script permissions..."
chmod +x .specify/scripts/bash/*.sh 2>/dev/null || true

echo ""
echo "✅ Cloud environment initialized"
echo "================================================"

exit 0
```

### 3. Feature 狀態檔結構

建立 `.specify/state/` 目錄，狀態檔格式：

```json
{
  "feature_id": "009-speckit-cloud",
  "branch": "009-speckit-cloud",
  "phase": "specify",
  "paths": {
    "spec": "specs/009-speckit-cloud/spec.md",
    "plan": null,
    "tasks": null
  },
  "created_at": "2026-01-29T10:00:00Z",
  "last_updated": "2026-01-29T10:00:00Z",
  "environment": {
    "created_in": "local",
    "last_modified_in": "cloud"
  }
}
```

### 4. 狀態管理函數

在 `.specify/scripts/bash/common.sh` 加入：

```bash
# ============================================
# State Management Functions
# ============================================

STATE_DIR="$REPO_ROOT/.specify/state"
STATE_FILE="$STATE_DIR/current-feature.json"

# 確保狀態目錄存在
ensure_state_dir() {
  mkdir -p "$STATE_DIR"
}

# 讀取當前 feature 狀態
get_current_feature_state() {
  if [ -f "$STATE_FILE" ]; then
    cat "$STATE_FILE"
  else
    echo "{}"
  fi
}

# 更新 feature 狀態
update_feature_state() {
  local feature_id="$1"
  local branch="$2"
  local phase="$3"

  ensure_state_dir

  local environment="local"
  if [ "$CLAUDE_CODE_REMOTE" = "true" ]; then
    environment="cloud"
  fi

  local now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  # 讀取現有狀態或建立新狀態
  if [ -f "$STATE_FILE" ]; then
    # 更新現有狀態
    jq --arg phase "$phase" \
       --arg env "$environment" \
       --arg now "$now" \
       '.phase = $phase | .last_updated = $now | .environment.last_modified_in = $env' \
       "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
  else
    # 建立新狀態
    cat > "$STATE_FILE" << EOF
{
  "feature_id": "$feature_id",
  "branch": "$branch",
  "phase": "$phase",
  "paths": {
    "spec": "specs/$feature_id/spec.md",
    "plan": null,
    "tasks": null
  },
  "created_at": "$now",
  "last_updated": "$now",
  "environment": {
    "created_in": "$environment",
    "last_modified_in": "$environment"
  }
}
EOF
  fi
}

# 更新狀態檔中的路徑
update_feature_path() {
  local path_key="$1"
  local path_value="$2"

  if [ -f "$STATE_FILE" ]; then
    jq --arg key "$path_key" \
       --arg value "$path_value" \
       '.paths[$key] = $value' \
       "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
  fi
}

# 清除當前 feature 狀態
clear_feature_state() {
  if [ -f "$STATE_FILE" ]; then
    rm "$STATE_FILE"
  fi
}
```

### 5. Skill 提示詞更新範本

在每個 speckit skill 的開頭加入環境偵測說明區塊：

```markdown
## Cloud Environment Support

此 skill 支援在 Claude Code Cloud 環境執行。

### 環境偵測

執行前，檢查執行環境：

```bash
echo $CLAUDE_CODE_REMOTE
```

- 如果輸出 `true`，表示在 Cloud 環境
- 如果為空，表示在本地環境

### Cloud 環境特殊處理

如果在 Cloud 環境：

1. **確認分支**：
   ```bash
   git branch --show-current
   ```
   如果不是目標 feature 分支，先切換：
   ```bash
   git fetch origin
   git checkout <feature-branch>
   ```

2. **檢查狀態檔**：
   讀取 `.specify/state/current-feature.json` 了解現有 feature 狀態

3. **完成後**：
   - 更新狀態檔
   - Commit 並 push 變更
   ```bash
   git add .
   git commit -m "Update feature state"
   git push
   ```
```

---

## 工作流程

### 情境 1：本地開發 → Cloud 執行

```bash
# 1. 本地啟動 feature
/speckit.specify Add user authentication

# 2. 推送分支到遠端（必要！Cloud 需要從 GitHub clone）
git push -u origin HEAD

# 3. 將任務發送到 Cloud 繼續
& Continue implementing the authentication feature based on the plan.
& First checkout the 009-user-auth branch, then run /speckit.plan

# 4. 監控進度
/tasks
```

### 情境 2：直接在 Cloud 執行

```bash
# 從命令列啟動
claude --remote "Checkout branch 009-user-auth and run /speckit.plan to create the implementation plan"
```

### 情境 3：Cloud → 本地（teleport）

```bash
# 方式 1：互動式選擇
/teleport

# 方式 2：指定 session ID
claude --teleport <session-id>

# 方式 3：從 /tasks 選擇
/tasks
# 然後按 't' teleport 到選定的 session
```

### 情境 4：平行開發

```bash
# 同時在多個 feature 上工作
& Checkout branch 009-user-auth and implement login API tests
& Checkout branch 010-caching and design cache invalidation strategy
& Checkout branch 011-logging and add structured logging to auth module

# 各自獨立執行，使用 /tasks 監控所有進度
/tasks
```

---

## 修改檔案清單

| 檔案 | 操作 | 說明 |
|------|------|------|
| `.claude/settings.json` | 修改 | 加入 SessionStart hook |
| `.specify/scripts/bash/cloud-init.sh` | 新增 | Cloud 環境初始化腳本 |
| `.specify/state/` | 新增目錄 | 狀態檔目錄 |
| `.specify/state/.gitkeep` | 新增 | 保持目錄存在 |
| `.specify/scripts/bash/common.sh` | 修改 | 加入狀態檔讀寫函數 |
| `.claude/commands/speckit.specify.md` | 修改 | 加入 Cloud 環境說明 |
| `.claude/commands/speckit.plan.md` | 修改 | 加入狀態檔更新邏輯 |
| `.claude/commands/speckit.tasks.md` | 修改 | 加入狀態檔更新邏輯 |
| `.claude/commands/speckit.implement.md` | 修改 | 加入狀態檔更新邏輯 |

---

## 驗證方式

### 1. 本地模擬 Cloud 環境

```bash
# 設定環境變數
export CLAUDE_CODE_REMOTE=true

# 測試初始化腳本
.specify/scripts/bash/cloud-init.sh

# 執行 skill（觀察是否正確處理 Cloud 環境）
/speckit.specify Test feature for cloud

# 清除環境變數
unset CLAUDE_CODE_REMOTE
```

### 2. 實際 Cloud 測試

```bash
# 發送簡單任務到 Cloud
claude --remote "List files in .specify/ directory and show the contents of .specify/memory/constitution.md"

# 發送 speckit 任務
claude --remote "Run /speckit.specify cloud-integration-test with description: Test cloud integration for speckit"
```

### 3. 跨環境測試

```bash
# 步驟 1：本地建立 feature
/speckit.specify Cloud integration test

# 步驟 2：推送到遠端
git push -u origin HEAD

# 步驟 3：Cloud 繼續
& Checkout branch XXX-cloud-integration-test and run /speckit.plan

# 步驟 4：Teleport 回本地
/teleport

# 步驟 5：驗證狀態同步
cat .specify/state/current-feature.json
```

### 4. Hook 測試

```bash
# 在新的 Cloud session 中測試 hook 是否正確執行
claude --remote "Check if cloud-init.sh ran by looking for the initialization messages in the output"
```

---

## 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| 分支衝突 | Cloud clone 錯誤分支 | 狀態檔記錄 branch，Cloud 啟動時檢查並提示切換 |
| 狀態不同步 | 本地和 Cloud 狀態不一致 | 每次操作後更新狀態檔並 commit/push |
| 腳本權限問題 | 腳本無法執行 | SessionStart hook 自動 `chmod +x` |
| Git 代理限制 | 某些 git 操作可能受限 | 測試所有必要 git 操作在 Cloud 可用 |
| Hook 未執行 | 環境未正確初始化 | 在 skill 中加入手動初始化指令作為備援 |
| jq 不可用 | 狀態檔解析失敗 | 提供 sed/grep 備援方案或簡化狀態格式 |

---

## 未來擴展

### 可能的增強功能

1. **自動分支切換**：SessionStart hook 自動切換到狀態檔記錄的分支
2. **進度追蹤 Dashboard**：建立 web dashboard 顯示所有 feature 的進度
3. **Slack/Discord 通知**：Cloud session 完成時發送通知
4. **多人協作**：支援多人同時在不同環境處理同一 feature 的不同 phase

### 需要等待的 Cloud 功能

1. **GitLab 支援**：目前僅支援 GitHub
2. **雙向 Session 傳輸**：目前只能 Cloud → 本地

---

## 參考資源

- [Claude Code on the web](https://code.claude.com/docs/en/claude-code-on-the-web)
- [Hooks configuration](https://code.claude.com/docs/en/hooks)
- [Settings reference](https://code.claude.com/docs/en/settings)
- [Security](https://code.claude.com/docs/en/security)
