# 多工具相容性規範 (Multi-Tool Compatibility)

## 核心要求

在進行任何功能規劃（Planning）、規格撰寫（Specs）、設計（Design）或實作（Implementation）時，**必須同時考慮並支援**以下 AI CLI 工具：

- **Claude Code**: 主要研發與執行工具。
- **GitHub Copilot CLI**: 輔助程式碼生成介面。
- **Gemini CLI**: 高性能模型整合。
- **Codex**: 替代執行引擎。

## 規劃與設計原則

1. **工具感測 (Tool-Awareness)**:
   - 所有的 Hook 腳本必須能偵測當前環境。
   - 識別變數：優先檢查 `GEMINI_PROJECT_DIR` (Gemini CLI) -> `CLAUDE_PROJECT_DIR` (Claude Code) -> Fallback `PWD`。
   - 工具名稱：根據環境變數顯示正確的工具名稱（如 "Claude Code" 或 "Gemini CLI"）。

2. **跨平台相容性**:
   - 設定檔路徑應避免硬編碼。使用 `~/.claude/` 或 `~/.gemini/` 等對應工具的目錄。
   - 若為通用設定，應放置於 `~/.config/ai-notify/` 等中立位置。

3. **介面標準化**:
   - 腳本與工具應優先支援 **Standard Input (stdin)** 接收 JSON 資料，這對 Claude Code 的 Hook 尤為重要。
   - 提供標準的 CLI 參數介面，確保可被各類 AI 工具透過 shell 呼叫。

4. **文件完備性**:
   - 每一項新功能的 `proposal.md` 或 `README.md` 必須包含以上工具的配置說明（若適用）。
   - 測試案例必須包含在不同工具環境下的驗證流程。

## 實作準則

- **Idempotency**: 安裝與更新腳本必須是冪等的（重複執行無害）。
- **Silent Fail**: Hook 腳本在背景執行時，失敗不應阻斷 AI CLI 的主要流程。
- **Modern UI**: 通知或輸出訊息應統一格式，支援 Emoji 與清晰的欄位劃分，提供一致的視覺體驗。
