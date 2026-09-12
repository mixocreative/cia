# cia — 程式碼完整性審查 Skill（Code Integrity Auditor）

[![tests](https://github.com/mixocreative/cia/actions/workflows/tests.yml/badge.svg)](https://github.com/mixocreative/cia/actions/workflows/tests.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![GitHub stars](https://img.shields.io/github/stars/mixocreative/cia?style=social)](https://github.com/mixocreative/cia/stargazers)

**這是一款 AI 程式助理的 skill，專門審查程式碼庫的「元件串接與骨幹架構」（wiring），而不是只看單一 function 做得對不對：像是寫了卻沒人讀的設定檔、`SELECT` 時有過濾但 `UPDATE` 時忘記加上去的條件、吞掉 Exception 還直接放行的 try-catch、明明什麼都沒檢查卻回報「0 錯誤」的 watchdog，或是前端畫面上根本長不出來的死角狀態。底層基於 Stafford Beer 的可行系統模型（Viable System Model, VSM）。適用於任何軟體專案；若需要電商/金物流相關的審查，請使用姐妹專案 [`ecommerce-cia`](../ecommerce-cia)。**

[English README](README.en.md) · Claude Code · Codex · Cursor · 任何看得懂 `SKILL.md` 的 AI agent

## 一句話講完核心理念

Linter、型態檢查工具（type checker）和單元測試（unit test）一次都只看一小塊程式碼。但真正能在這些關卡存活下來的 Bug，幾乎都藏在元件「之間」：例如在前一步被凍結快取的數值，到了下一步卻又去讀即時資料；寫了控制邏輯卻沒有任何下游消費；或是背景 job 執行失敗時吐出的狀態竟然跟成功一模一樣。這個 skill 會先將每個元件對映到 Viable System Model 的 System 1–5，接著透過 22 條審查路線（sweeps）走訪元件之間的對接管道。重點是，每條路線都必須精確指出涉案檔案並引用實際程式碼——絕不能只用幾筆數字糊弄過去。鐵律第一條：**絕不允許默默死掉（nothing dies silently）。**

## 如何使用

```bash
git clone https://github.com/mixocreative/cia ~/.claude/skills/cia      # 或 ~/.codex/skills/cia
# 在任何專案中輸入：
#   "pre-launch audit, Screen tier"      -> 執行六步驟審查協定
#   "run tests"                          -> 執行測試、回報數量，並詢問是否進行審查
#   "something broke"                    -> 診斷前先探測，用最小幅度修復並附上測試
```

它會全自動跑完所有流程（包含 `docker up`、從 lockfile 安裝套件、啟動 dev server、自動化瀏覽器走訪），只有在遇到真的無法自行處理的事情時才會向你求助——而且會直接給你能複製貼上的完整指令。修復 Bug 時，每個 Finding 都會獨立發一個 commit，並附上能夠抓到該 Bug 的測試案例；至於任何不可逆操作或影響共用狀態的變更，則會列為升級事項並附上 patch 檔供你確認。

## 審查結束後你會拿到什麼

一份架構清晰的報告，開頭就是 5 行白話摘要，讓專案負責人能立刻動手處置；接著依序為：VSM 系統地圖、每條 sweep 的檢測結果（含問題位置與程式碼引用）、主機能力對照表、檢測器點名（確定安全防護網真的有在運作）、固定格式的問題清單（包含嚴重程度、信心度、邊界條件與驗證測試），以及已被證實運作正常的控制項。

## 專案目錄結構

```
SKILL.md              導航路由、執行階段發現、六步驟協定、自主權階梯、審查路線索引、
                      問題升級機制、白話條款契約、選單
references/
  sweeps.md           S1–S22 審查路線，包含檢測方法、評分標準、報告單行格式
  theory.md           套用到程式碼庫的 VSM 理論：System 1, 2, 3, 3*, 4, 5
  doctrine.md         證據評級、內容探索、通用測試矩陣、領域檢核表
  context-templates.md Blender 外掛程式 · 電商平台 · 工作流編排（workflow orchestration）
  reporting.md        Finding 產出格式、嚴重程度模型、經驗證的控制項、最終報告
tools/sweep-diff.py   比對本 skill 與 ecommerce-cia 審查路線的差異
tests/fixture-service 包含 10 個已知 Bug 與標準答案的 Python job runner；測試指引見 tests/RUNBOOK.md
```

## 來源與品質驗證

這裡的每一條審查路線（sweep），都是過去在已上線的專案中實戰踩過的坑。當時儘管測試全過（green suite）、Analyser 與 Linter 完全沒有警告，這些 Bug 依然悄悄存在——我們在發現的當天就把經驗紀錄下來。其中與電商領域相關的學問放到了 `ecommerce-cia`，通用的部分則保留在這裡。這兩個 skill 都由全新的 AI agent 在附帶標準答案的測試專案上進行冷啟動測試（`tests/RUNS.md`）。

License: MIT.