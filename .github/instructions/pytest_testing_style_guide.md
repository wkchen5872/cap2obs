# Pytest Testing Style Guide

**版本**：1.0  
**適用範圍**：全團隊 Python 專案  
**風格類型**：**Tests outside the code**（pytest 官方推薦 + src layout）  
**最後更新**：2026 年 3 月

### 1. 目的
本指南定義團隊統一的 pytest 測試撰寫風格，目的是讓測試程式碼**一致、可讀、易維護**，並符合現代 Python 最佳實務。

本指南主要參考：
- Google Python Style Guide
- flake8-pytest-style（PT 規則）
- pytest 官方 Good Integration Practices

### 2. 核心原則

- **強制使用 pytest**：禁止使用 `unittest` 模組或繼承 `unittest.TestCase`。
- 測試函數一律使用**模組層級**定義：`def test_xxx():`（**不要**包在 class 裡）。
- **斷言**：一律使用**裸斷言**（bare assert），例如：
  ```python
  assert result == expected
  assert len(items) == 5
  ```
- 例外測試：使用 `with pytest.raises(ExpectedException):`
- Mock：使用 `unittest.mock.patch`（decorator 或 context manager 皆可）。
- 測試應保持簡單：一個測試函數原則上只驗證**一件事情**（AAA 模式：Arrange → Act → Assert）。

### 3. 專案目錄結構（推薦 A - Tests outside the code）

測試目錄 `tests/` 與 `src/` **放在專案根目錄同一階層**。這是 pytest 官方強烈推薦的布局，特別適合使用 src layout 的專案。

**標準結構範例**：

```
project-root/
├── src/
│   └── mypackage/                  # 你的主要套件（可安裝的生產程式碼）
│       ├── __init__.py
│       ├── fetch_data.py
│       ├── utils.py
│       └── core/
│           └── processor.py
├── tests/                          # ← 測試與 src/ 同階層
│   ├── __init__.py                 # 建議保留
│   ├── test_fetch_data.py
│   ├── test_utils.py
│   └── core/
│       └── test_processor.py
├── pyproject.toml
├── pytest.ini                      # 或配置放在 pyproject.toml
├── README.md
└── .gitignore
```

**優點**：
- 清楚區分生產程式碼與測試程式碼
- 打包發布時容易排除 tests
- 避免 import 混淆（不會誤 import 本地開發程式碼）
- 符合 pytest 官方最佳實務

### 4. 命名規範（參考 Google Python Style Guide）

- **測試檔案**：`test_*.py`（強烈推薦）或 `*_test.py`
- **測試函數**：使用清晰描述性的名稱，格式建議：
  - `test_<被測功能>_<情境>_<預期結果>`
  - 範例：
    - `test_calculate_total_with_valid_input_returns_correct_value`
    - `test_fetch_data_when_api_returns_500_raises_http_error`
- **測試模組 docstring**：**不需要**。只有在有特殊執行方式、外部依賴或不尋常的 setup 時才加入。

### 5. flake8-pytest-style 重要規則（團隊強制遵守）

請安裝 `flake8-pytest-style`（或使用 ruff 對應規則），以下為重點規則：

#### Fixture 相關
- 使用 `@pytest.fixture`（**不要加括號**）
- 使用 keyword arguments 設定 scope 等參數
- 有回傳值的 fixture：名稱**不要**加底線 `_`
- 沒有回傳值的 fixture（純 side-effect）：名稱**加上**底線 `_`，或改用 `@pytest.mark.usefixtures`
- 使用 `yield` 處理 teardown；沒有 teardown 時改用 `return`

#### parametrize
- 避免重複的測試案例
- 正確使用 names 與 values 的型別（建議 list of tuples）

#### Assert 與例外
- **禁止** 使用 `self.assertEqual` 等 unittest-style assertions（PT009）
- `pytest.raises()` 必須指定具體例外類型，並建議加上 `match=`
- `pytest.raises()` 區塊內保持**單一簡單陳述式**
- 複合 assert 請拆成多個獨立 assert

#### 其他
- 使用 `import pytest`（不要 `from pytest import ...`）
- `@pytest.mark.xxx` **不要加括號**
- 測試函數參數**不要**設定預設值

### 6. 配置範例（pyproject.toml）

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
addopts = [
    "-q",
    "--tb=short",
    "--strict-markers",
    "--strict-config"
]

[tool.ruff]          # 推薦使用 ruff（更快）
select = ["PT"]      # 開啟 pytest style 規則
# ignore = ["PT001"] # 如有特定規則想關閉，可在此設定

[tool.black]
line-length = 88
```

### 7. 執行測試指令（從專案根目錄執行）

```bash
# 一般執行
python -m pytest tests/ -q

# 更簡潔（推薦日常使用）
python -m pytest -q --tb=no

# 執行特定測試檔
python -m pytest tests/test_fetch_data.py -q
```

### 8. 額外建議
- Fixture 盡量放在 `tests/conftest.py`（依 scope 決定層級）
- 複雜的測試資料可放在 `tests/data/` 目錄
- 所有 decorator 都應該有對應的 unit test
- 保持測試獨立：不要讓一個測試依賴另一個測試的執行結果

---

**團隊承諾**：  
所有新撰寫的測試程式碼必須符合本指南。若有特殊情況無法遵守，請在 PR 中說明並與 Reviewer 討論。

如需範例程式碼、Fixture 寫法、parametrize 實際範例，或調整特定規則，請隨時提出。