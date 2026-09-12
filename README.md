# cia — Code Integrity Auditor｜程式碼完整性稽核 Skill

[![tests](https://github.com/mixocreative/cia/actions/workflows/tests.yml/badge.svg)](https://github.com/mixocreative/cia/actions/workflows/tests.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Claude Code plugin](https://img.shields.io/badge/Claude_Code-plugin-D97757)](#install安裝) [![Codex skill](https://img.shields.io/badge/OpenAI_Codex-skill-000000)](#install安裝) [![GitHub stars](https://img.shields.io/github/stars/mixocreative/cia?style=social)](https://github.com/mixocreative/cia/stargazers)

**English 🇬🇧 · 繁體中文 🇹🇼** — every section is written in both, English first, 中文接在後面。

A skill for Claude Code and OpenAI Codex that audits a codebase as a **viable system** in Stafford Beer's sense, and hunts the defect class that only such a view can see: **cross-boundary invariant violations**, also called **integration-level** or **emergent defects**.

> 這是給 Claude Code 與 OpenAI Codex 使用的 Skill。它將整套程式碼視為 Stafford Beer 所定義的「可存活系統」（Viable System）來進行稽核，專門抓出只有從這個視野才能發現的 bug：**跨邊界不變量違反**（cross-boundary invariant violations），亦即**整合層級缺陷**或**湧現缺陷**。這類 bug 不會單獨存在於任何一個函式中，而是藏在兩個「各自運作正常」的函式交界處。

Since v2.0 the skill is a runbook plus reference files: twenty-two sweeps instead of fourteen, depth tiers so a run says what it did and did not walk, sweep lines that name their sites and quote a line from one of them, a plain-language contract for owners who are not engineers, a paired run with `ecommerce-cia`, and a fixture project with an answer key that fresh agents are cold-tested against.

> 自 v2.0 起，本 Skill 已演進為一套 Runbook 搭配參考文件：掃描項目（Sweeps）從原本的 14 項擴增至 22 項；導入深度分級機制（Depth Tiers），讓每次執行都能清楚交代檢視與未檢視的範圍；掃描結果行會直接標示檔案位置並引用相關程式碼；針對非工程背景的 Owner 提供白話文合約機制；支援與 `ecommerce-cia` 協同執行；並附帶包含標準答案的測試專案（Fixture），用於對全新的 Agent 進行冷測試（Cold test）。

## How this is different from a code review｜與一般 Code Review 的差異

**Ordinary code review, linters and AI "review my code" tools find coding errors**: a typo, a null that was not checked, a function that returns the wrong type, a style violation, a bug inside one function. They read the code and ask *is this line written correctly?*

**This skill checks whether the logic actually works as a whole.** It asks *when this runs, does the system do what you think it does?* It follows one value from where it is written to every place it is later read. It follows one switch from the admin screen to the line of code that is supposed to obey it. It checks whether "tests passed" means the tests actually ran.

| | Ordinary code review / linter｜一般 Review / Linter | This skill｜本 Skill |
|---|---|---|
| Question asked｜核心提問 | Is each line written correctly?｜每一行程式碼寫得對不對？ | Does the whole thing behave the way you think?｜整體實際運作是否符合預期？ |
| Unit of inspection｜檢查範圍 | one file, one function｜單一檔案、單一函式 | one value across time, one switch across layers｜跨時間的值演變、跨架構層級的開關 |
| Finds｜能抓出的問題 | syntax, types, null checks, style, a bug inside a function｜語法、型別、Null 值、Style 規範、函式內部的 bug | a switch nobody reads, a check forgotten before the action, a green report that skipped the real tests, a vendor field read wrong｜沒任何程式讀取的無用開關、檢查完卻沒再確認就動作、並未真正執行測試卻回報通過的綠燈、對第三方廠商欄位解析錯誤 |
| Cannot find｜無法抓出的問題 | anything that lives *between* two correct functions｜任何夾在兩個正確函式*之間*的邏輯漏洞 | (it starts there)｜（這正是本 Skill 發揮作用之處） |
| Proof it accepts｜採認的驗證標準 | "tests pass"｜「測試通過」即可 | the exact run line with counts, or "not verified"｜必須有實際跑過的行數數據，否則一律標示為「未驗證」 |

Both are needed. Run the linter for the lines. Run this for the logic.

> **一般的 Code Review、Linter 以及各類「幫你看程式碼」的 AI 工具，重點都在找寫錯的地方**：例如打錯字、漏掉 Null 檢查、回傳型別錯誤、格式不合規範，或是單一函式內部的 bug。它們閱讀程式碼時，問的問題是：「這行程式碼有沒有寫對？」
>
> **而本 Skill 則是直接稽核整套邏輯是否真能正常連動。** 它問的是：「系統實際執行時，運作方式真的跟你想的一樣嗎？」它會追蹤變數：從寫入點一路追到後續每一個讀取點；它會追蹤開關：從後台設定畫面一路追到理論上該受控的那一行程式碼；它也會嚴格審查「測試通過」到底是不是真的有落實執行。
>
> 兩者相輔相成。Linter 負責顧好每一行程式碼，這個 Skill 則負責掌控整體邏輯。

## In plain words｜白話文解釋（非技術人員版）

Think of any piece of software as a small company. Some staff **do the work** (handle a request, save a record, send an email). Some **keep the workers from tripping over each other** (queues, locks, "one at a time" rules). A **manager's settings panel** tells the workers what is switched on. An **auditor** checks the books. Someone **reads the outside world's rulebooks** (a bank's API spec, a vendor's file format). And an **owner** decides what happens when something goes wrong.

Most code-checking tools ask: *does each employee do their own job correctly?* This skill asks: *do they actually talk to each other, and at the right time?* Three real-shaped examples:

1. **The manager flips a switch in the settings panel. Nobody on the floor is listening.** The switch exists, the code behind it is fine, and no running code ever reads it. Every piece is "correct". The feature the manager thinks is off is still on. This skill calls it a *dead control* and checks every setting against the code that is supposed to obey it.
2. **A clerk checks that a seat is free, walks to the desk, then books it without looking again.** Two clerks do this at once; two people get the same seat. Each clerk followed procedure. The gap between "check" and "act" is where the bug lives. *Time-of-check to time-of-use race.*
3. **The auditor says "all good!" but only opened the pages that were on the desk.** The pages in the locked cabinet were skipped because the key was missing that day. The report is green and means nothing. *Vacuous pass.* This skill treats every skipped test as "not verified", never as "passed".

What it does, in order: draws the org chart of your code first (who does the work, who coordinates, who sets policy, who audits, who faces the outside), then checks every conversation between them, then tells you exactly which conversation is broken, in which file, on which line, and how to fix it.

> 請將一套軟體想像成一家小公司。裡面有**第一線員工**負責執行實務（處理 Request、存取資料、寄發 Email）；有**主管**負責協調，不讓大家撞在一起（包含排隊機制、加鎖鎖定、「一次一人」的規則）；有**店長的控制面板**用來開關各種功能；有**稽核會計**負責定期查帳；有**專人負責研究外部規則**（例如銀行的 API 規格書、物流廠商的檔案格式）；最後還有**老闆**負責決定系統出事時的應變政策。
>
> 多數檢查程式碼的工具問的是：*每個員工有沒有把自己的工作做對？* 這個 Skill 問的則是：*員工之間到底有沒有正確溝通？而且時間點對不對？* 以下是三個實際發生的情境：
>
> 1. **店長在控制面板關掉了一個開關，但樓下員工完全沒收到通知。** 設定開關確實存在，後端程式碼也寫得沒錯，卻沒有任何執行中的程式去讀取這個設定。每個部分單獨看都「正確」，店長以為已停用的功能其實仍在背景運作。本 Skill 將這種狀況稱為**死開關**，會主動拿每一項設定去比對「到底有沒有程式碼在聽它命令」。
> 2. **櫃台先確認座位有空，接著走到座位區準備劃位，期間卻沒再確認一次就直接訂下去。** 若兩個櫃台同時這樣操作，就會導致兩人訂到同一個座位。每個櫃台各自都按流程走，bug 卻出在「檢查」與「執行」之間的空隙。這就是**檢查與使用之間的競態條件（Race Condition）**。
> 3. **會計回報「帳目完全沒問題！」，但實際上只翻了桌上隨手可拿的幾頁。** 鎖在櫃子裡的重點帳冊只因當天找不到鑰匙就被直接跳過。查帳報告顯示一片綠燈，卻毫無參考價值。這就是**空洞的測試通過**。本 Skill 會將所有被跳過的測試直接判定為「未驗證」，絕不盲目給予通過標籤。
>
> 本 Skill 的執行順序為：先繪製出整套程式碼的組織架構圖（區分執行層、協調層、政策層、稽核層以及對外介面），接著逐一檢查各層級之間的每一條溝通管道，最後精準回報哪條管道斷線、位於哪個檔案的第幾行，並提供修復建議。

## Watch it run｜實際執行示範

![/cia demo](docs/demo.gif)

Real, unedited output of `/cia` in demo mode on a production PHP/ProcessWire shop: runtime discovery, the codebase mapped onto VSM Systems 1–5 with its channels, then two sweeps. It found a System 3 → System 1 channel that bypasses the app's own cron control plane, with file:line evidence and the fix. Replayed as a typed terminal for the recording; the text is the model's.

> 上圖為 `/cia` 在某個正式營運中的 PHP/ProcessWire 電商專案執行 Demo 模式的真實輸出內容，完全未經修改：系統先自動探索專案的運作機制，將程式碼對應至 VSM 的 System 1–5 架構並列出所有傳輸通道，隨後執行兩次完整掃描。它成功抓出一條繞過應用程式本身排程控制面的 System 3 → System 1 隱藏通道，並附上 `file:line` 的佐證程式碼與修復方案。示範影片採用打字終端機重播，所有文字皆由模型即時生成。

## The theory｜架構理論

Beer's Viable System Model (*Brain of the Firm*, 1972; *The Heart of Enterprise*, 1979) states that anything which stays alive in a changing environment has the same five-part structure, repeated at every level of recursion:

> Stafford Beer 所提出的可存活系統模型（Viable System Model, VSM；參見《Brain of the Firm》1972、《The Heart of Enterprise》1979）主張：任何能夠在動態環境中持續生存的系統，都具備一套相同的五層結構，且每個遞迴層級的結構完全一致：

| System｜系統層級 | Role｜架構角色 | In a codebase｜對應至程式碼中的元件 |
|---|---|---|
| **1** | does the work｜實際執行層 | request handlers, domain services, workers｜Request 處理器、Domain Services、背景運算 Task |
| **2** | damps oscillation between the parts of System 1｜協調層（防止 System 1 各元件互相衝突） | locks, queues, deadlines, idempotency keys, ordering｜Lock 機制、Queue 佇列、Timeout 期限、冪等鍵（Idempotency Keys）、執行順序控制 |
| **3** | commands and allocates resources to System 1｜管制與資源分配層（向 System 1 下達指令） | settings, feature flags, admin pages, config files｜控制台設定、Feature Flags、後台管理頁面、Config 檔 |
| **3\*** | audits System 1 directly, bypassing its own reports｜獨立稽核層（不採信 System 1 的自我回報，直接進行查帳） | test suites, probes, reconciliation scripts｜測試套件、Health Check 探測腳本、資料對帳腳本 |
| **4** | faces the environment and the future｜外部環境與未來規劃層 | vendor specs, external APIs, webhooks, callbacks｜第三方廠商 API 規格書、外部 API 串接、Webhook、Callback |
| **5** | identity and policy; receives the algedonic (pain) signal｜身份識別與政策層（負責接收「痛覺」警訊並決策） | defaults, catch-block posture, kill switches, fail-closed rules｜預設配置、Catch 區塊的處置邏輯、熔斷機制（Circuit Breaker）、Fail-closed 降級規則 |

The systems are joined by **channels**. Ashby's Law of Requisite Variety says a channel must carry as much variety as the thing it regulates, otherwise the control it claims to exercise is fictional. Beer's diagnosis of a failing organisation is almost never "a department is incompetent"; it is "a channel is missing, saturated, or bypassed".

> 系統與系統之間依靠**通道（Channel）**相連。根據 Ashby 的必要多樣性定律（Law of Requisite Variety）：控制通道所能承載的變化量，必須大於或等於受控對象產生的變化量，否則該「控制」便流於形式。Beer 在診斷出問題的組織時，結論幾乎從不是「某個部門能力不足」，而是「某條溝通通道遺失、阻塞，或是被直接繞過了」。

Software fails the same way. Every function can be correct and the system still not viable, because a channel between two correct pieces is broken: a System 3 setting no System 1 code reads, a System 3\* suite that reports green because the tests touching the store never ran, a System 4 field interpreted against the code's belief rather than the vendor's definition, a System 1 step that re-reads System 3 live after an earlier step froze a snapshot. Static analysis, linters and unit suites inspect one piece at a time and therefore cannot see a channel by construction.

> 軟體系統崩潰的方式完全相同。即使每個函式寫得完全正確，系統依然可能無法運作，原因往往出在兩個正常元件之間的通道中斷了：例如寫了 System 3 設定卻完全沒有任何 System 1 的程式碼去讀取；或是 System 3\* 的測試套件因為碰不到資料庫而跳過測試，卻回報全綠通過；或是 System 4 欄位未按廠商規範，而是依憑工程師主觀想像去解析；又或是 System 1 在前置步驟已凍結了快照，後續步驟卻又跑去讀取即時的 System 3 資料。靜態分析工具、Linter 和單元測試一次都只觀察單點，因此從架構視野上天生就無法察覺通道中斷的問題。

This skill was built after exactly that happened on a production shop: four money-path defects, all between correctly written functions, all invisible to a green suite, all found by a second auditor who traced channels instead of reading functions.

> 這個 Skill 的開發初衷，正是源於一次真實發生的線上慘劇：某個正式營運的電商網站，其付款流程中隱藏了四個致命缺陷。這四個問題全部夾在寫得毫無瑕疵的函式之間，自動化測試顯示全綠通過卻完全沒抓到，最後是第二位稽核人員透過「追蹤通道」而非「閱讀函式」才成功找出問題。

## The stance this skill takes from Beer｜繼承自 Beer 的核心立場

- **The purpose of a system is what it does** (POSIWID). Not what the docs, the comments or the admin screen say it does. An audit reads behaviour, and treats the written intent as a hypothesis to test against the running system.
  > **系統的真實目的，就是它實際呈現出來的行為**（POSIWID）。既非文件記載、註解說明，也不是後台畫面所宣稱的功能。稽核時只看實際行為，寫下來的設計意圖一律視為待驗證的假說。
- **Recursion.** Every System 1 unit is itself a viable system with its own 1–5. A payment module has its own control, its own audit, its own policy; the audit descends one level and asks the same five questions again.
  > **遞迴結構（Recursion）。** 每個 System 1 單元本身就是一個獨立的可存活系統，具備專屬的 1–5 結構。例如一個金流模組擁有自己的控制、稽核與政策機制；稽核下鑽至下一層時，同樣重複詢問這五個核心問題。
- **Variety engineering.** Complexity is not removed, it is absorbed or amplified. Every guard, validator, idempotency key and state machine is a variety attenuator; every default and fallback is an amplifier of whatever the environment throws in. Ask of each: does it match the variety of what it faces?
  > **多樣性工程（Variety Engineering）。** 複雜度不會憑空消失，只會被吸收或放大。每一個 Guard 條件、驗證器、冪等鍵、狀態機都在削減系統的變化量；而每一個預設值與 Fallback 降級機制，則是在放大外界傳入的未知變數。針對每個機制都必須審查：它是否有能力承受所面臨的變化量？
- **Autonomy with cohesion.** System 1 must be free to act without asking System 3 on every step (a checkout that blocks on live config on every request is not autonomous), yet System 3 must still be able to command it (a toggle nothing reads is not cohesion). Both failures are channel failures.
  > **自主性與一致性的平衡。** System 1 必須具備不需每步請示 System 3 就能直接執行的能力（若每次結帳 Request 都被即時讀取的 Config 檔卡住，就不算具備自主性），但 System 3 依然要能有效控制它（從不讀取的開關就不具備一致性）。這兩種失敗本質上都是通道失效。
- **The auditor is System 3\*.** This skill is the channel that bypasses the system's own reports. A green suite is System 3's report about itself; the audit exists precisely because that report can be vacuous.
  > **稽核者的定位即為 System 3\*。** 本 Skill 扮演的就是那條繞過系統自我診斷、直接深入查核的通道。全綠通過的測試只是 System 3 的自我診斷報告；而稽核機制之所以必要，正是因為這份報告可能存在虛報或漏測。
- **Algedonic signals must reach System 5.** A pain signal that stops in a log file has not reached policy. Every alert, every catch block, every refund path is traced to the point where identity decides.
  > **痛覺訊號必須成功傳遞至 System 5。** 若痛覺訊號僅停留在 Log 檔案中，就代表它從未抵達政策決策層。每一個 Alarm 警報、每一個 Catch 處理區塊、每一條退款流程，都必須一路追蹤到「最終由誰進行決策」的關鍵節點。

## How the theory becomes procedure｜從理論轉化為實際稽核流程

1. **Map the codebase onto Systems 1–5 first** (§0.9 step 0) and report the table: every component, its primary system, its channels as `producer → consumer`.
2. **Walk the channels** with twenty-two mandatory sweeps (§0.9); each defect class below is a named kind of broken channel, and each sweep enumerates its sites from the map rather than from grep.
3. **Grade viability, not just correctness**: §2 asks whether each of the five systems exists, whether System 3\* is independent of System 3, whether an algedonic path reaches System 5, whether variety is matched.
4. **Report structurally**: every finding names its defect class and the VSM channel it sits on.

> 1. **將程式碼對應至 System 1–5 架構**（§0.9 第 0 步），輸出結構化地圖：標示每個元件、其所屬的主要系統，以及對應的傳輸通道（`producer → consumer`）。
> 2. **沿著通道進行深度排查**：執行二十二項強制掃描（§0.9）。後續列出的每種缺陷類型，本質上都是某種具名的通道中斷狀況；每個掃描檢查點皆建構自架構地圖，而非盲目使用 Grep 搜尋。
> 3. **評估標準為「系統能否持續存活」，而非僅看「語法是否正確」**：§2 負責確認五個系統層級是否完備、System 3\* 是否獨立於 System 3 運作、痛覺傳導路徑是否能抵達 System 5，以及系統承載的多樣性變化量是否匹配。
> 4. **產出結構化稽核報告**：每個發現的漏洞皆須明確標註其缺陷類型以及對應的 VSM 通道位置。

## The defect classes it hunts｜專門獵捕的缺陷類型：跨邊界不變量違反

These are **cross-boundary invariant violations**: integration-level, emergent defects where every function is correct and the bug lives between them. Each sweep in section 0.9 names one; every finding states its defect class and its boundary location as `producer → consumer`:

> 以下皆屬於**跨邊界不變量違反**：各個函式單獨看都正確，bug 卻藏在函式之間的接縫處。§0.9 的每個掃描項目皆對應一種類型；每一筆發現項目都會詳細列出缺陷分類與邊界位置（`producer → consumer`）：

| Term｜專業術語 | Meaning｜詳細定義 |
|---|---|---|
| **TOCTOU race**｜檢查與使用之間的競態條件（TOCTOU） | a predicate checked at one step, dropped at the step that acts｜某個條件在檢查當下成立，但在實際執行動作時該條件已失效 |
| **Temporal coupling / stale snapshot**｜時間耦合／過期快照（Temporal Coupling / Stale Snapshot） | a value frozen at one moment, re-read live by a later reader｜資料值在特定時間點被凍結成快照，後續的讀取端卻又重新抓取了即時狀態 |
| **Semantic drift**｜語意漂移（Semantic Drift） | code's reading of an external field diverges from the vendor spec｜程式碼對外部欄位涵義的理解，與第三方廠商提供的規格書不一致 |
| **Dead control**｜死開關（Dead Control） | an admin toggle or flag no runtime path consumes｜後台介面設有控制開關，但在實際的程式執行路徑中卻從未讀取該設定 |
| **Fail-open default**｜出錯就放行（Fail-Open Default） | an error path that proceeds as if the read succeeded｜錯誤處理路徑誤將 Exception 當作讀取成功，導致程式繼續盲目向下執行 |
| **Vacuous pass**｜空洞的通過（Vacuous Pass） | a suite that says OK because the meaningful tests skipped or never ran｜測試報告顯示 OK，但實際上核心測試項目被 Skip 掉或根本未曾跑過 |
| **Deferred-work residue**｜「之後補」的殘骸（Deferred-Work Residue） | a "follow-up commit" comment that never landed｜程式碼註解承諾會在未來的 Commit 補上邏輯，但實際上永遠沒補 |
| **Rename residue**｜改名殘骸（Rename Residue） | a consumer still bound to the old name｜變數或 API 已改名，但呼叫端的程式碼仍綁定在舊名稱上 |
| **Diagnosis without probe**｜沒探測就下診斷（Diagnosis Without Probe） | a cause concluded from an error message, not a direct check｜僅憑錯誤訊息盲目猜測問題主因，並未進行實際的探測與數據驗證 |
| **Boundary schema drift**｜邊界結構漂移（Boundary Schema Drift） | a payload acted on before its shape and type are validated｜跨越邊界傳入的資料，在未經形狀與型別驗證的情況下就被直接使用 |
| **Cascade / retry storm**｜連鎖失敗／重試風暴（Cascade / Retry Storm） | one step's failure or retry becomes a crash, duplicate write, or orphaned side effect｜單一步驟失敗或重試引發連鎖崩潰、重複寫入，或是殘留孤兒狀態的副作用 |
| **Orphan capability**｜孤立功能（designed-but-unbuilt，已設計但未實作） | a class, table, column or design-document promise with no caller, no writer, no page and no gap-register row｜類別、資料表、欄位或設計文件承諾的功能，完全沒有呼叫端、寫入者、畫面頁面，也沒有記錄在 Gap Register |
| **Scope shadow**｜範圍陰影（Scope Shadow） | an audit of one diff or module whose report reads as whole-system green｜只稽核了單一 Diff 或模組，產出的報告卻顯示全系統通關（Green） |
| **Corner disagreement**｜四角認知不一致（Corner Disagreement） | the parties that hold one object — user, operator, external provider, database — describe it differently; or a built capability is unreachable under the shipped configuration｜持有同一物件的各方（使用者、營運人員、外部第三方服務商、資料庫）對其描述不一；或是已開發的功能在正式發布的設定下根本無法存取 |
| **Control enforced elsewhere**｜控制項在別處執行 | a setting claims to restrict a choice made on a page the system does not render, where the request cannot express it｜某項設定宣稱能限制買家在「別人的頁面」（系統自己不渲染的頁面）上做的選擇，但送出的 Request 根本表達不了那個限制 |
| **Sampled, not enumerated**｜以抽樣代替枚舉 | one cell of the contract read and generalised to the grid; a later finding disproves the method, not just the answer｜僅讀取合約中的其中一格就推廣至整個矩陣；後續發現證明是方法論本身錯誤，而不只是答案不對 |
| **Environment constraint never crossed**｜環境約束未交叉驗證 | a dependency's requirement on the host and the host's capability both written down, never multiplied｜套件/依賴對 Host 的要求與 Host 本身的能力雖均有記錄，卻從未進行交叉相乘驗證 |
| **Blind instrument**｜盲檢工具（Blind Instrument） | a check that stopped running or examined nothing, whose report looked identical to a clean one｜已經停止執行或根本沒檢查任何東西的檢查項目，產出的報告卻與無瑕疵（Clean）報告完全相同 |
| **Unrendered surface**｜未渲染的介面 | a state the system can reach has no screen, or one nobody rendered, or one no person can dismiss｜系統可達到的狀態卻沒有對應畫面、或是沒人渲染該畫面、或是沒有任何使用者可以關閉該畫面 |
| **Vacuous or too-late proof**｜無效或太遲的驗證 | a test asserting emptiness passes for an unrelated reason; or the guard sits so deep in a slow suite nobody reaches it｜斷言空值的測試因無關原因而通過；或是防禦機制放在執行極慢的測試集深處，根本沒人執行得到 |

Prompt with any of those terms, or "audit the wiring and runtime behaviour, not the code", and the sweeps run first.

> 當 Prompt 中出現上述任何一個專有名詞，或是提及「稽核接線與實際行為，不要只看程式碼靜態內容」時，系統即會優先觸發對應的掃描流程。

## Which channel each sweep walks｜各掃描項目與 VSM 通道的對應關係

Each defect class above is a broken channel between two VSM systems; the sweeps are organised by channel, not by file:

> 每種缺陷本質上都是兩個 VSM 系統之間中斷的通道；因此掃描作業是依據通道進行分類，而非依檔案劃分：

| Channel｜通道分類 | Sweeps that walk it｜負責排查此通道的掃描項目 |
|---|---|
| System 3 → System 1 (control to consumer)｜控制端至使用端（Control-to-Consumer） | dead control, deferred-work residue, stale snapshot |
| System 1 → System 1 across time｜跨時間維度（Cross-Time） | TOCTOU race, rename residue |
| System 4 ↔ environment｜對外部環境介面（Environment） | semantic drift, boundary schema drift |
| System 3\* → System 3｜稽核端至控制端（Audit-to-Control） | vacuous pass, diagnosis without probe |
| System 5 defaults｜政策預設值（Policy Default） | fail-open, cascade / retry storm |
| System 3 → System 4 (a setting that must reach a page you do not render)｜System 3 → System 4（必須傳送到未渲染頁面的設定） | control enforced elsewhere, sampled-not-enumerated｜控制項在別處執行、以抽樣代替枚舉 |
| System 4 requirement × target environment｜System 4 需求 × 目標環境 | environment constraint never crossed｜環境約束未交叉驗證 |
| System 3\* on itself (is the safety net still looking?)｜針對 System 3\* 本身的檢查（安全網是否仍在運作？） | blind instrument, vacuous or too-late proof｜盲檢工具、無效或太遲的驗證 |
| Every party that holds the object｜持有該物件的各方 | corner disagreement (the four-corner walk), terminal-state accountability｜四角認知不一致（四角走查）、終態責任歸屬 |
| System 1 → a screen someone opens｜System 1 → 使用者開啟的畫面 | unrendered surface, orphan capability, scope shadow｜未渲染的介面、孤立功能、範圍陰影 |

A channel on the map with no sweep site named against it is reported as unswept.

> 只要架構地圖上有任何一條通道未被掃描點覆蓋，報告中將直接標示為「未掃描」。

## What it does｜本 Skill 的實際工作內容

Given a repository, the skill:

1. **Discovers the project's runtime bindings itself** (test runner, canonical environment, dev server, credentials file) and announces them before judging anything.
2. **Maps the codebase onto the VSM (§0.9 step 0), then runs twenty-two mandatory sweeps (§0.9)** along that map's channels, catching the defect classes a green suite cannot.
3. **Applies a universal integrity doctrine**: evidence grading, context discovery, a Viable System Model governance pass, a universal test matrix from happy path through recovery, a domain checklist, and a severity model.
4. **Executes the six-step pre-launch protocol (§0.6) autonomously**: fast lint and scope tests, doctrine audit, full suite in the canonical environment, runtime walk in a real browser or CLI, fix-or-escalate, numbered report with explicit deferrals.
5. **Never green-lights on partial evidence.** Every skipped step carries the reason and the exact command the owner must run. Skipped DB tests are reported as unverified, never as green.
6. **Declares a depth tier** (Screen / Walk / Full) in the first line of every report; anything the tier excluded is reported as unverified, never omitted.
7. **Names its sites.** A sweep line is a path list plus one quoted line from one of them — a count alone is the vacuous pass this skill exists to catch.
8. **Runs paired with `ecommerce-cia` on request**: one discovery, one map, one line per sweep, no duplicated finding.

> 提供一個 Repository 給它，它會自動執行以下流程：
>
> 1. **自動探索專案的運作機制**（包含測試指令、正式環境、開發伺服器、憑證設定檔），並在做出任何判斷前先明確宣告已知資訊。
> 2. **先繪製 VSM 架構圖（§0.9 第 0 步），接著沿著通道執行二十二項強制掃描（§0.9）**，精準抓出全綠測試也無法察覺的深層缺陷。
> 3. **嚴格套用通用完整性教條**：包含證據等級分類、情境探索、VSM 治理檢查、從正常路徑到災難復原的通用測試矩陣、領域檢查清單，以及嚴謹的嚴重度評估模型。
> 4. **自主執行六階段部署前稽核流程（§0.6）**：包含快速 Lint 與範圍測試、教條稽核、正式環境完整測試、真實瀏覽器或 CLI 實測、能自動修復就修復否則立即上報，最後產出附帶明確保留項目的編號報告。
> 5. **證據不足時絕不盲目放行。** 每個被跳過的步驟都會附上原因，以及需要管理者手動執行的指令。被跳過的資料庫測試一律標記為「未驗證」，絕不給予綠燈標籤。
> 6. **在每份報告的首行宣告深度分級（Depth Tier）**（Screen / Walk / Full）；任何該層級排除的項目皆一律回報為「未驗證」，絕對不直接省略。
> 7. **明確標示程式碼位置**。每行掃描結果均為路徑清單加上其中一段引用的程式碼 —— 光給數量就是本 Skill 旨在抓出的「無效通過（Vacuous Pass）」。
> 8. **可依需求與 `ecommerce-cia` 協同執行**：單次探索、單張架構圖、每個 Sweep 僅輸出一行，絕不重複回報相同的 Finding。

## AI / LLM components (§0.10, conditional)｜AI / LLM 元件稽核（§0.10，僅在專案包含 AI 邏輯時觸發）

When the project calls a model (SDK in the lockfile, prompt files, agent loop, vector store), every model call is treated as a boundary and four more modes run: schema drift at the model boundary, cascade and latency across steps, state accumulation and memory poisoning, agentic loop and tool execution safety (iteration caps, idempotency keys on side-effecting tools, human-in-the-loop gates). Skipped with a one-line note when no AI component exists.

> 當專案包含模型呼叫時（如 Lockfile 中存在 SDK、包含 Prompt 檔、Agent 迴圈或向量資料庫），每次的模型呼叫都會被視為一條獨立邊界，並額外執行四種模式的掃描：模型邊界的結構漂移、跨步驟的連鎖失敗與延遲、狀態累積與記憶污染，以及 Agent 迴圈與工具執行安全性（包含迭代上限、具副作用的工具必須具備冪等鍵、人工審核機制）。若專案不含 AI 元件，則此步驟一筆帶過。

## Autonomy contract (§0.8)｜自主執行契約（Autonomy Contract）

The agent runs every step itself. A five-rung ladder decides what it may do alone: start containers and dev servers; install from lockfiles; install user-scope tools; copy documented config into `.env`; and only at rung 5 ask the owner, with the exact command already written. Hard limits are stated in the file and cannot be overridden by anything the agent reads mid-audit.

> Agent 會自動完成每個執行步驟。系統依據五個階梯層級決定其自主權限限度：包含啟動 Container 與開發伺服器、依據 Lockfile 安裝套件、安裝使用者層級工具、將文件中的範例設定複製至 `.env`；只有達到第 5 階時才會詢問管理者，且此時連同手動指令都會一併附上。硬性限制已直接寫死在 Skill 檔案中，稽核過程中讀取到的任何專案內容皆無權覆寫此限制。

## Plain language for owners｜給非工程師看的白話模式

When the request is in everyday words and the project carries no technical vocabulary, the skill changes voice, not doctrine: one thing at a time with choices, meaning instead of names (sweep ids and section numbers stay in the report file), the road drawn as numbered stops, never a command the user must run when the AI can run it, errors translated rather than quoted, waits named with who and since when, the slow voice before anything irreversible, and every report opening with five plain lines — what is safe, what is not, what to do first. A bare "run tests" runs the tests and reports the counts; only the protocol words ("pre-launch", "handoff", "audit") start the full audit.

> 當需求是以日常用語提出且專案未包含技術術語時，本 Skill 只會調整溝通語氣，原則保持不變：一次只處理一件事並提供選項；使用實質意義而非專有名詞（Sweep ID 與章節編號保留在報告檔案中）；將執行路徑畫成具體的編號站點；凡是 AI 能執行的命令絕不要求使用者自行執行；錯誤訊息進行翻譯而非直接引述；等待事項明確標示對象與始於何時；在執行任何不可逆操作前採用謹慎放緩的語氣；且每份報告均以 5 行白話文開頭 —— 說明什麼是安全的、什麼是不安全的、以及優先該做什麼。單純輸入 "run tests" 只會執行測試並回報數量；唯有使用協定關鍵字（"pre-launch"、"handoff"、"audit"）才會啟動完整的稽核流程。

## Tested against a fixture, by fresh agents｜用有標準答案的專案冷測試

`tests/fixture-service/` is a small Python job runner with ten planted defects under four green tests — a config key nothing reads, a SELECT-then-UPDATE that drops its predicate, a config loader that fails open, a monitor that prints "0 problems" while examining nothing, a heartbeat nothing reads, a state the status page cannot show, an orphaned retry helper, a vacuous test, a test that leaks into the runner's environment. `tests/EXPECTED.md` is the answer key; `tests/RUNBOOK.md` scores a run (hit, near, miss, false positive, control misfiled, vacuous line); `tests/RUNS.md` is the ledger. The fixture is deliberately not a shop, so it also proves the commerce gate stays closed and that "run tests" does not start a four-hour protocol. `tools/sweep-diff.py` shows where this skill's sweep texts and `ecommerce-cia`'s have diverged.

> `tests/fixture-service/` 是一個小型 Python 任務執行器（Job Runner），在 4 個綠燈測試下埋藏了 10 個缺陷 —— 包含無任何程式讀取的 Config Key、遺失條件的 SELECT-then-UPDATE 查詢、預設放行的 Config Loader、什麼都沒檢查卻印出 "0 problems" 的 Monitor、無人讀取的 Heartbeat、狀態頁面無法顯示的狀態、孤立的 Retry Helper、無效測試（Vacuous Test），以及會洩漏至 Runner 環境的測試。`tests/EXPECTED.md` 為標準答案；`tests/RUNBOOK.md` 用於為執行結果評分（Hit、Near、Miss、False Positive、Control Misfiled、Vacuous Line）；`tests/RUNS.md` 則是紀錄帳冊。該 Fixture 刻意不設計成電商系統，藉此證明金流關卡保持關閉，且執行 "run tests" 不會啟動長達四小時的完整協定。`tools/sweep-diff.py` 則可用來比對本 Skill 與 `ecommerce-cia` 的 Sweeps 內文是否產生偏差。

## Install｜安裝方式

**Claude Code, as a plugin (recommended)｜使用 Claude Code 外掛安裝（推薦）：**

```
claude plugin marketplace add mixocreative/cia
claude plugin install cia@mixocreative
```

Or inside a session: `/plugin` → marketplaces → add `mixocreative/cia` → install `cia`.
> 或在對話介面中輸入：`/plugin` → marketplaces → 新增 `mixocreative/cia` → 安裝 `cia`。

The skill is now a runbook (`SKILL.md`) plus reference files, so clone the repository rather than copying one file:

> 本 Skill 目前是一套 Runbook（`SKILL.md`）搭配多份參考文件，因此請直接 Clone 本儲存庫，而不是只複製單一檔案：

**Claude Code, as a skill directory｜手動放置 Skill 目錄：**

```
git clone https://github.com/mixocreative/cia ~/.claude/skills/cia
```

**OpenAI Codex：**

```
git clone https://github.com/mixocreative/cia ~/.codex/skills/cia
```

Install the companion [ecommerce-cia](https://github.com/mixocreative/ecommerce-cia) alongside it; the protocol invokes both, separately.
> 請一併安裝姊妹 Skill [ecommerce-cia](https://github.com/mixocreative/ecommerce-cia)；流程執行時會分別呼叫這兩個 Skill。

## Use｜使用方式

```
/cia
```

It also auto-selects on pre-launch vocabulary: "run the tests", "prepare for handoff", "green-light", "audit", "ready for launch". On a transactional commerce project it runs, then tells you to also invoke the companion skill [ecommerce-cia](https://github.com/mixocreative/ecommerce-cia) for the commerce-domain doctrine it does not own. The two skills never merge or auto-load each other.

> 當提及「跑測試」、「準備交接」、「可以上線了嗎」、「進行稽核」等關鍵字時，系統會自動觸發。若為交易型電商專案，它會優先執行，隨後提醒你呼叫姊妹 Skill [ecommerce-cia](https://github.com/mixocreative/ecommerce-cia) 來處理其未涵蓋的電商專屬教條。這兩個 Skill 永遠保持獨立，絕不會自動合併或相互自動載入。
>
> 亦支援繁體中文 Prompt 觸發，例如：「用 VSM 幫我稽核這個專案」、「檢查設定頁的開關有沒有真的被程式讀到」、「追一下這個值從寫入到每個讀取的地方」、「測試說通過，幫我確認真的有跑」。

## Companion｜姊妹 Skill

[ecommerce-cia](https://github.com/mixocreative/ecommerce-cia) — the same execution spine plus checkout, payment, inventory, refund, digital-entitlement and Taiwan-gateway (ECPay / NewebPay) doctrine.

> [ecommerce-cia](https://github.com/mixocreative/ecommerce-cia)：採用相同的執行骨架，額外針對結帳、金流、庫存、退款、數位商品權限，以及台灣在地金流（綠界／藍新）設有專章檢查。

## Structure｜檔案結構

| File｜檔案 | Purpose｜功能用途 |
|---|---|
| `SKILL.md` | the runbook: routing, runtime discovery, six-step protocol, autonomy ladder, sweep index, escalation, plain-language contract, start menu｜Runbook 本體：包含路由、執行期探索、六步驟協定、自主階梯、Sweep 索引、通報升級機制、白話文合約與啟動選單 |
| `references/sweeps.md` | S1–S22 with methods, gradings and report-line formats｜S1–S22 掃描項目，包含檢測方法、評級標準與報告輸出格式 |
| `references/theory.md` | the Viable System Model applied to a codebase; Systems 1, 2, 3, 3*, 4, 5｜應用於程式碼庫的 Viable System Model（可行系統模型）；涵蓋 Systems 1, 2, 3, 3*, 4, 5 |
| `references/doctrine.md` | evidence grading, context discovery, the universal test matrix, the domain checklist｜證據評級、上下文探索、通用測試矩陣、領域檢查清單 |
| `references/context-templates.md` | Blender add-on · e-commerce platform · workflow orchestration｜Blender 外掛 · 電商平台 · 工作流編排 |
| `references/reporting.md` | finding format, severity model, verified controls, the final report｜Finding 格式、嚴重度模型、已驗證控制項與最終報告 |
| `tools/sweep-diff.py`, `tests/` | drift check against the sibling; the fixture service, answer key, run book and ledger｜與兄弟專案的比對工具；測試專案（Fixture Service）、標準答案、Runbook 與紀錄帳冊 |

## License｜授權條款

MIT
