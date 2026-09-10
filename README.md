# cia — Code Integrity Auditor｜程式碼完整性稽核技能

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Claude Code plugin](https://img.shields.io/badge/Claude_Code-plugin-D97757)](#install安裝) [![Codex skill](https://img.shields.io/badge/OpenAI_Codex-skill-000000)](#install安裝) [![GitHub stars](https://img.shields.io/github/stars/mixocreative/cia?style=social)](https://github.com/mixocreative/cia/stargazers)

**English 🇬🇧 · 繁體中文 🇹🇼** — every section is written in both, English first, 中文接在後面。

A skill for Claude Code and OpenAI Codex that audits a codebase as a **viable system** in Stafford Beer's sense, and hunts the defect class that only such a view can see: **cross-boundary invariant violations**, also called **integration-level** or **emergent defects**.

> 這是一個給 Claude Code 與 OpenAI Codex 用的技能（Skill）。它把一套程式碼當成 Stafford Beer 所說的「可存活系統」（Viable System）來稽核，專門找一種只有從這個角度才看得到的 bug：**跨邊界不變量違反**（cross-boundary invariant violations），也叫**整合層級缺陷**或**湧現缺陷**。這種 bug 不在任何一個函式裡，而是在兩個「各自都正確」的函式之間。

## How this is different from a code review｜這跟一般的程式碼審查差在哪

**Ordinary code review, linters and AI "review my code" tools find coding errors**: a typo, a null that was not checked, a function that returns the wrong type, a style violation, a bug inside one function. They read the code and ask *is this line written correctly?*

**This skill checks whether the logic actually works as a whole.** It asks *when this runs, does the system do what you think it does?* It follows one value from where it is written to every place it is later read. It follows one switch from the admin screen to the line of code that is supposed to obey it. It checks whether "tests passed" means the tests actually ran.

| | Ordinary code review / linter｜一般審查、linter | This skill｜這個技能 |
|---|---|---|
| Question asked｜問的問題 | Is each line written correctly?｜每一行有沒有寫對？ | Does the whole thing behave the way you think?｜整體跑起來是不是你以為的那樣？ |
| Unit of inspection｜檢查單位 | one file, one function｜一個檔案、一個函式 | one value across time, one switch across layers｜一個值跨時間、一個開關跨層 |
| Finds｜找得到 | syntax, types, null checks, style, a bug inside a function｜語法、型別、空值、風格、函式內的 bug | a switch nobody reads, a check forgotten before the action, a green report that skipped the real tests, a vendor field read wrong｜沒人讀的開關、動作前忘了再檢查、跳過真正測試的綠燈報告、讀錯的廠商欄位 |
| Cannot find｜找不到 | anything that lives *between* two correct functions｜任何住在兩個正確函式*之間*的問題 | (it starts there)｜（它就從這裡開始） |
| Proof it accepts｜接受的證據 | "tests pass"｜「測試通過」 | the exact run line with counts, or "not verified"｜真正跑過的那行數字，否則就是「未驗證」 |

Both are needed. Run the linter for the lines. Run this for the logic.

> **一般的程式碼審查、linter、還有各種「幫我看程式碼」的 AI 工具，找的是寫錯的地方**：打錯字、沒檢查空值、回傳型別不對、風格不符、某個函式裡的 bug。它們讀程式碼，問的是「這一行有沒有寫對？」
>
> **這個技能查的是整套邏輯到底有沒有真的在運作。** 它問的是「實際跑起來的時候，系統做的事是不是你以為的那樣？」它追一個值：從寫入的地方追到後面每一個讀它的地方。它追一個開關：從後台畫面追到應該聽它的那一行程式碼。它查「測試通過」是不是真的有跑。
>
> 兩種都需要。linter 管每一行，這個技能管邏輯。

## In plain words｜白話版（給非工程師）

Think of any piece of software as a small company. Some staff **do the work** (handle a request, save a record, send an email). Some **keep the workers from tripping over each other** (queues, locks, "one at a time" rules). A **manager's settings panel** tells the workers what is switched on. An **auditor** checks the books. Someone **reads the outside world's rulebooks** (a bank's API spec, a vendor's file format). And an **owner** decides what happens when something goes wrong.

Most code-checking tools ask: *does each employee do their own job correctly?* This skill asks: *do they actually talk to each other, and at the right time?* Three real-shaped examples:

1. **The manager flips a switch in the settings panel. Nobody on the floor is listening.** The switch exists, the code behind it is fine, and no running code ever reads it. Every piece is "correct". The feature the manager thinks is off is still on. This skill calls it a *dead control* and checks every setting against the code that is supposed to obey it.
2. **A clerk checks that a seat is free, walks to the desk, then books it without looking again.** Two clerks do this at once; two people get the same seat. Each clerk followed procedure. The gap between "check" and "act" is where the bug lives. *Time-of-check to time-of-use race.*
3. **The auditor says "all good!" but only opened the pages that were on the desk.** The pages in the locked cabinet were skipped because the key was missing that day. The report is green and means nothing. *Vacuous pass.* This skill treats every skipped test as "not verified", never as "passed".

What it does, in order: draws the org chart of your code first (who does the work, who coordinates, who sets policy, who audits, who faces the outside), then checks every conversation between them, then tells you exactly which conversation is broken, in which file, on which line, and how to fix it.

> 把任何一套軟體想成一家小公司。有人**做事**（處理請求、存資料、寄信）。有人**負責不讓大家撞在一起**（排隊、上鎖、「一次一個」的規則）。有一個**店長的設定面板**告訴大家哪些功能是開的。有一個**會計**查帳。有人**負責讀外面世界的規則書**（銀行的 API 規格、廠商的檔案格式）。還有一個**老闆**決定出事的時候怎麼辦。
>
> 大部分檢查程式碼的工具問的是：*每個員工有沒有把自己的工作做對？* 這個技能問的是：*他們之間有沒有真的在講話，而且是在對的時間講？* 三個真實形狀的例子：
>
> 1. **店長在設定面板按了一個開關，樓下沒有人在聽。** 開關存在，它背後的程式碼也沒錯，但沒有任何執行中的程式去讀它。每一段都「正確」。店長以為關掉的功能其實還開著。這個技能叫它**死開關**，會把每一個設定拿去對照「應該聽它的那段程式碼」。
> 2. **櫃台先確認座位是空的，走到櫃檯，然後不再看一眼就直接訂下去。** 兩個櫃台同時這樣做，兩個人拿到同一個位子。每個櫃台都照程序走。bug 住在「檢查」跟「動作」之間的縫裡。**檢查與使用之間的競態。**
> 3. **會計說「都沒問題！」但只翻了桌上那幾頁。** 上鎖櫃子裡的那幾頁因為那天鑰匙不見就跳過了。報告全綠，但什麼都不代表。**空洞的通過。** 這個技能把每一個被跳過的測試都當成「未驗證」，絕不當成「通過」。
>
> 它做的事依序是：先畫出你程式碼的組織圖（誰做事、誰協調、誰定政策、誰查帳、誰面對外面），再檢查他們之間每一段對話，最後告訴你哪一段對話斷了、在哪個檔案、第幾行、怎麼修。

## Watch it run｜看它跑一次

![/cia demo](docs/demo.gif)

Real, unedited output of `/cia` in demo mode on a production PHP/ProcessWire shop: runtime discovery, the codebase mapped onto VSM Systems 1–5 with its channels, then two sweeps. It found a System 3 → System 1 channel that bypasses the app's own cron control plane, with file:line evidence and the fix. Replayed as a typed terminal for the recording; the text is the model's.

> 上面是 `/cia` 在一個正式營運的 PHP/ProcessWire 電商上跑 demo 模式的真實輸出，一字未改：先自動探索專案怎麼跑，把程式碼對應到 VSM 的 System 1–5 並列出通道，接著跑兩個掃描。它找到一條繞過應用程式自家排程控制面的 System 3 → System 1 通道，附 file:line 證據與修法。錄影是用打字終端機重播，文字全部是模型自己產生的。

## The theory｜理論

Beer's Viable System Model (*Brain of the Firm*, 1972; *The Heart of Enterprise*, 1979) states that anything which stays alive in a changing environment has the same five-part structure, repeated at every level of recursion:

> Stafford Beer 的可存活系統模型（Viable System Model, VSM；《Brain of the Firm》1972、《The Heart of Enterprise》1979）主張：任何能在變動環境中活下來的系統，都有同一套五部分結構，而且每一層遞迴都長一樣：

| System｜系統 | Role｜角色 | In a codebase｜在程式碼裡是什麼 |
|---|---|---|
| **1** | does the work｜做事的 | request handlers, domain services, workers｜請求處理、領域服務、背景工作 |
| **2** | damps oscillation between the parts of System 1｜防止 System 1 各部分互相打架 | locks, queues, deadlines, idempotency keys, ordering｜鎖、佇列、期限、冪等鍵、順序 |
| **3** | commands and allocates resources to System 1｜下命令、分配資源給 System 1 | settings, feature flags, admin pages, config files｜設定、功能旗標、後台頁面、設定檔 |
| **3\*** | audits System 1 directly, bypassing its own reports｜不看 System 1 自己的報告，直接查帳 | test suites, probes, reconciliation scripts｜測試套件、探測腳本、對帳腳本 |
| **4** | faces the environment and the future｜面對外部環境與未來 | vendor specs, external APIs, webhooks, callbacks｜廠商規格書、外部 API、webhook、回呼 |
| **5** | identity and policy; receives the algedonic (pain) signal｜身分與政策；接收「痛覺」訊號 | defaults, catch-block posture, kill switches, fail-closed rules｜預設值、catch 區塊的態度、緊急開關、出錯就關閉的規則 |

The systems are joined by **channels**. Ashby's Law of Requisite Variety says a channel must carry as much variety as the thing it regulates, otherwise the control it claims to exercise is fictional. Beer's diagnosis of a failing organisation is almost never "a department is incompetent"; it is "a channel is missing, saturated, or bypassed".

> 系統之間靠**通道**（channel）相連。Ashby 的必要多樣性定律說：通道能承載的變化量，必須跟它要控制的東西一樣多，否則那個「控制」只是假的。Beer 診斷一個出問題的組織，結論幾乎從來不是「某個部門很爛」，而是「某條通道不見了、塞住了、或被繞過了」。

Software fails the same way. Every function can be correct and the system still not viable, because a channel between two correct pieces is broken: a System 3 setting no System 1 code reads, a System 3\* suite that reports green because the tests touching the store never ran, a System 4 field interpreted against the code's belief rather than the vendor's definition, a System 1 step that re-reads System 3 live after an earlier step froze a snapshot. Static analysis, linters and unit suites inspect one piece at a time and therefore cannot see a channel by construction.

> 軟體壞掉的方式一模一樣。每個函式都可以是對的，系統還是活不下去，因為兩個正確的部分之間有一條通道斷了：一個沒有任何 System 1 程式讀的 System 3 設定；一個因為碰資料庫的測試根本沒跑所以回報全綠的 System 3\* 測試套件；一個照程式碼自己的想像、而不是照廠商定義去解讀的 System 4 欄位；一個前面步驟已經凍結快照、後面步驟卻重新讀即時 System 3 的 System 1。靜態分析、linter、單元測試一次只看一塊，所以從結構上就看不到通道。

This skill was built after exactly that happened on a production shop: four money-path defects, all between correctly written functions, all invisible to a green suite, all found by a second auditor who traced channels instead of reading functions.

> 這個技能的起點就是這件事真的發生了：一個正式上線的電商，付款路徑上四個缺陷，全部在寫得正確的函式之間，全綠的測試全部看不到，全部是第二位稽核者靠「追通道」而不是「讀函式」找到的。

## The stance this skill takes from Beer｜從 Beer 繼承的立場

- **The purpose of a system is what it does** (POSIWID). Not what the docs, the comments or the admin screen say it does. An audit reads behaviour, and treats the written intent as a hypothesis to test against the running system.
  > **系統的目的就是它實際做的事**（POSIWID）。不是文件、註解或後台畫面說它做的事。稽核讀的是行為；寫下來的意圖只是待驗證的假設。
- **Recursion.** Every System 1 unit is itself a viable system with its own 1–5. A payment module has its own control, its own audit, its own policy; the audit descends one level and asks the same five questions again.
  > **遞迴。** 每一個 System 1 單元本身又是一個可存活系統，有自己的 1–5。一個金流模組有自己的控制、稽核與政策；稽核往下一層，再問一次同樣五個問題。
- **Variety engineering.** Complexity is not removed, it is absorbed or amplified. Every guard, validator, idempotency key and state machine is a variety attenuator; every default and fallback is an amplifier of whatever the environment throws in. Ask of each: does it match the variety of what it faces?
  > **多樣性工程。** 複雜度不會消失，只會被吸收或放大。每個守衛、驗證器、冪等鍵、狀態機都是在削減變化量；每個預設值與 fallback 都是在放大外界丟進來的任何東西。對每一個都要問：它撐得住它面對的變化量嗎？
- **Autonomy with cohesion.** System 1 must be free to act without asking System 3 on every step (a checkout that blocks on live config on every request is not autonomous), yet System 3 must still be able to command it (a toggle nothing reads is not cohesion). Both failures are channel failures.
  > **自主但一致。** System 1 要能不必每一步都問 System 3 就動作（每個請求都卡在即時設定上的結帳不叫自主），但 System 3 仍要指揮得動它（沒人讀的開關不叫一致）。兩種失敗都是通道失敗。
- **The auditor is System 3\*.** This skill is the channel that bypasses the system's own reports. A green suite is System 3's report about itself; the audit exists precisely because that report can be vacuous.
  > **稽核者就是 System 3\*。** 這個技能就是那條繞過系統自我報告的通道。全綠的測試是 System 3 對自己的報告；稽核之所以存在，正是因為那份報告可能是空的。
- **Algedonic signals must reach System 5.** A pain signal that stops in a log file has not reached policy. Every alert, every catch block, every refund path is traced to the point where identity decides.
  > **痛覺訊號必須抵達 System 5。** 停在 log 檔裡的痛覺訊號沒有抵達政策層。每個警報、每個 catch 區塊、每條退款路徑，都要追到「由誰決定」的那一點。

## How the theory becomes procedure｜理論如何變成流程

1. **Map the codebase onto Systems 1–5 first** (§0.9 step 0) and report the table: every component, its primary system, its channels as `producer → consumer`.
2. **Walk the channels** with twelve mandatory sweeps (§0.9); each defect class below is a named kind of broken channel, and each sweep enumerates its sites from the map rather than from grep.
3. **Grade viability, not just correctness**: §2 asks whether each of the five systems exists, whether System 3\* is independent of System 3, whether an algedonic path reaches System 5, whether variety is matched.
4. **Report structurally**: every finding names its defect class and the VSM channel it sits on.

> 1. **先把程式碼對應到 System 1–5**（§0.9 第 0 步），輸出一張表：每個元件、它的主要系統、它的通道（`producer → consumer`）。
> 2. **沿通道走**：十二個強制掃描（§0.9）。下面每一種缺陷類型都是一種有名字的斷通道；每個掃描的檢查點來自地圖，不是來自 grep。
> 3. **評的是「活不活得下去」，不只是「對不對」**：§2 問五個系統各自存不存在，System 3\* 是否獨立於 System 3，痛覺路徑有沒有抵達 System 5，變化量有沒有對上。
> 4. **結構化回報**：每個發現都寫明缺陷類型與它所在的 VSM 通道。

## The defect classes it hunts｜它獵的缺陷類型：跨邊界不變量違反

These are **cross-boundary invariant violations**: integration-level, emergent defects where every function is correct and the bug lives between them. Each sweep in section 0.9 names one; every finding states its defect class and its boundary location as `producer → consumer`:

> 這些都是**跨邊界不變量違反**：每個函式都對，bug 住在函式之間。§0.9 每個掃描對應一種；每個發現都寫明缺陷類型與邊界位置（`producer → consumer`）：

| Term｜術語 | Meaning｜意思 |
|---|---|---|
| **TOCTOU race**｜檢查與使用之間的競態 | a predicate checked at one step, dropped at the step that acts｜某個條件在檢查時有，到動作時卻不見了 |
| **Temporal coupling / stale snapshot**｜時間耦合／過期快照 | a value frozen at one moment, re-read live by a later reader｜某個值在某一刻被凍結，後面的讀者卻重新讀即時值 |
| **Semantic drift**｜語意漂移 | code's reading of an external field diverges from the vendor spec｜程式碼對某個外部欄位的理解，跟廠商規格書不一樣 |
| **Dead control**｜死開關 | an admin toggle or flag no runtime path consumes｜後台有開關，沒有任何執行路徑讀它 |
| **Fail-open default**｜出錯就放行 | an error path that proceeds as if the read succeeded｜錯誤路徑當作讀取成功繼續往下走 |
| **Vacuous pass**｜空洞的通過 | a suite that says OK because the meaningful tests skipped or never ran｜測試顯示 OK，因為真正重要的測試被跳過或根本沒跑 |
| **Deferred-work residue**｜「之後補」的殘骸 | a "follow-up commit" comment that never landed｜註解說下個 commit 補，永遠沒補 |
| **Rename residue**｜改名殘骸 | a consumer still bound to the old name｜還綁在舊名字上的使用端 |
| **Diagnosis without probe**｜沒探測就下診斷 | a cause concluded from an error message, not a direct check｜從錯誤訊息猜原因，沒有直接去查 |
| **Boundary schema drift**｜邊界結構漂移 | a payload acted on before its shape and type are validated｜跨邊界進來的資料，形狀與型別還沒驗證就拿去用 |
| **Cascade / retry storm**｜連鎖失敗／重試風暴 | one step's failure or retry becomes a crash, duplicate write, or orphaned side effect｜一步失敗或重試，變成崩潰、重複寫入、或留下孤兒副作用 |

Prompt with any of those terms, or "audit the wiring and runtime behaviour, not the code", and the sweeps run first.

> 提示詞裡出現上面任何一個術語，或說「稽核接線與實際行為，不是只看程式碼」，掃描就會先跑。

## Which channel each sweep walks｜每個掃描走哪條通道

Each defect class above is a broken channel between two VSM systems; the sweeps are organised by channel, not by file:

> 每一種缺陷都是兩個 VSM 系統之間斷掉的通道；掃描是按通道組織的，不是按檔案：

| Channel｜通道 | Sweeps that walk it｜走這條通道的掃描 |
|---|---|
| System 3 → System 1 (control to consumer)｜控制到使用端 | dead control, deferred-work residue, stale snapshot |
| System 1 → System 1 across time｜跨時間 | TOCTOU race, rename residue |
| System 4 ↔ environment｜對外部環境 | semantic drift, boundary schema drift |
| System 3\* → System 3｜稽核對控制 | vacuous pass, diagnosis without probe |
| System 5 defaults｜政策預設值 | fail-open, cascade / retry storm |

A channel on the map with no sweep site named against it is reported as unswept.

> 地圖上任何一條沒有被掃描點對到的通道，會被回報為「未掃描」。

## What it does｜它做什麼

Given a repository, the skill:

1. **Discovers the project's runtime bindings itself** (test runner, canonical environment, dev server, credentials file) and announces them before judging anything.
2. **Maps the codebase onto the VSM (§0.9 step 0), then runs twelve mandatory sweeps (§0.9)** along that map's channels, catching the defect classes a green suite cannot.
3. **Applies a universal integrity doctrine**: evidence grading, context discovery, a Viable System Model governance pass, a universal test matrix from happy path through recovery, a domain checklist, and a severity model.
4. **Executes the six-step pre-launch protocol (§0.6) autonomously**: fast lint and scope tests, doctrine audit, full suite in the canonical environment, runtime walk in a real browser or CLI, fix-or-escalate, numbered report with explicit deferrals.
5. **Never green-lights on partial evidence.** Every skipped step carries the reason and the exact command the owner must run. Skipped DB tests are reported as unverified, never as green.

> 給它一個 repo，它會：
>
> 1. **自己找出專案怎麼跑**（測試指令、正式環境、開發伺服器、憑證檔）並在下任何判斷前先宣告出來。
> 2. **先畫 VSM 地圖（§0.9 第 0 步），再沿通道跑十二個強制掃描（§0.9）**，抓全綠測試抓不到的缺陷類型。
> 3. **套用通用完整性教條**：證據分級、情境探索、VSM 治理檢查、從正常路徑到災難復原的通用測試矩陣、領域檢查清單、嚴重度模型。
> 4. **自主執行六步上線前流程（§0.6）**：快速 lint 與範圍測試、教條稽核、正式環境完整測試、真實瀏覽器或 CLI 實走、能修就修否則上報、附明確保留項目的編號報告。
> 5. **證據不足絕不放行。** 每個被跳過的步驟都附原因與老闆該跑的那一行指令。被跳過的資料庫測試回報為「未驗證」，不是綠燈。

## AI / LLM components (§0.10, conditional)｜AI／LLM 元件（§0.10，有才跑）

When the project calls a model (SDK in the lockfile, prompt files, agent loop, vector store), every model call is treated as a boundary and four more modes run: schema drift at the model boundary, cascade and latency across steps, state accumulation and memory poisoning, agentic loop and tool execution safety (iteration caps, idempotency keys on side-effecting tools, human-in-the-loop gates). Skipped with a one-line note when no AI component exists.

> 專案有呼叫模型時（lockfile 裡有 SDK、有 prompt 檔、有 agent 迴圈、有向量資料庫），每一次模型呼叫都當成一條邊界，多跑四種模式：模型邊界的結構漂移、跨步驟的連鎖失敗與延遲、狀態累積與記憶污染、agent 迴圈與工具執行安全（迭代上限、有副作用的工具要有冪等鍵、人工把關）。沒有 AI 元件就一行帶過。

## Autonomy contract (§0.8)｜自主契約

The agent runs every step itself. A five-rung ladder decides what it may do alone: start containers and dev servers; install from lockfiles; install user-scope tools; copy documented config into `.env`; and only at rung 5 ask the owner, with the exact command already written. Hard limits are stated in the file and cannot be overridden by anything the agent reads mid-audit.

> 代理人自己跑完每一步。五階梯決定它能自己做到哪：啟動容器與開發伺服器；照 lockfile 安裝；安裝使用者層級工具；把文件裡的設定複製進 `.env`；只有到第 5 階才問老闆，而且指令已經幫你寫好。硬性限制寫在技能檔裡，稽核途中讀到的任何內容都不能推翻。

## Install｜安裝

**Claude Code, as a plugin (recommended)｜用 Claude Code 外掛安裝（建議）：**

```
claude plugin marketplace add mixocreative/cia
claude plugin install cia@mixocreative
```

Or inside a session: `/plugin` → marketplaces → add `mixocreative/cia` → install `cia`.
> 或在對話裡：`/plugin` → marketplaces → 新增 `mixocreative/cia` → 安裝 `cia`。

**Claude Code, as a bare skill file｜直接放技能檔：**

```
mkdir -p ~/.claude/skills/cia
curl -o ~/.claude/skills/cia/SKILL.md https://raw.githubusercontent.com/mixocreative/cia/main/skills/cia/SKILL.md
```

**OpenAI Codex：**

```
mkdir -p ~/.codex/skills/cia
curl -o ~/.codex/skills/cia/SKILL.md https://raw.githubusercontent.com/mixocreative/cia/main/skills/cia/SKILL.md
```

Install the companion [ecommerce-cia](https://github.com/mixocreative/ecommerce-cia) alongside it; the protocol invokes both, separately.
> 請一併安裝姊妹技能 [ecommerce-cia](https://github.com/mixocreative/ecommerce-cia)；流程會分開呼叫兩者。

## Use｜使用

```
/cia
```

It also auto-selects on pre-launch vocabulary: "run the tests", "prepare for handoff", "green-light", "audit", "ready for launch". On a transactional commerce project it runs, then tells you to also invoke the companion skill [ecommerce-cia](https://github.com/mixocreative/ecommerce-cia) for the commerce-domain doctrine it does not own. The two skills never merge or auto-load each other.

> 說「跑測試」、「準備交接」、「可以上線了嗎」、「稽核」時也會自動觸發。在交易型電商專案上它會先跑，再提醒你另外呼叫姊妹技能 [ecommerce-cia](https://github.com/mixocreative/ecommerce-cia) 處理它不負責的電商教條。兩個技能永遠不會合併或互相自動載入。
>
> 中文提示詞也可以，例如：「用 VSM 幫我稽核這個專案」、「檢查設定頁的開關有沒有真的被程式讀到」、「追一下這個值從寫入到每個讀取的地方」、「測試說通過，幫我確認真的有跑」。

## Companion｜姊妹技能

[ecommerce-cia](https://github.com/mixocreative/ecommerce-cia) — the same execution spine plus checkout, payment, inventory, refund, digital-entitlement and Taiwan-gateway (ECPay / NewebPay) doctrine.

> [ecommerce-cia](https://github.com/mixocreative/ecommerce-cia)：同一套執行骨架，加上結帳、金流、庫存、退款、數位商品權限，以及台灣金流（綠界／藍新）專章。

## Structure of skills/cia/SKILL.md｜技能檔結構

| Section｜章節 | Purpose｜用途 |
|---|---|
| 0 | Routing hard rules, trigger vocabulary, runtime discovery, six-step protocol, overrides, autonomy contract, mandatory sweeps｜路由硬規則、觸發詞彙、執行環境探索、六步流程、專案覆寫、自主契約、強制掃描 |
| 1 | Fundamental audit doctrine: outcomes over technologies, evidence before accusation, version-aware external facts｜稽核基本教條：看結果不看技術、先證據再指控、外部事實要對版本 |
| 2 | Viable System Model governance pass (Systems 1–5)｜VSM 治理檢查（System 1–5） |
| 3–6 | Context discovery and context templates｜情境探索與情境模板 |
| 7 | Universal test matrix｜通用測試矩陣 |
| 8 | Domain audit checklist｜領域檢查清單 |
| 9–10 | Finding format and severity model｜發現格式與嚴重度模型 |

## License｜授權

MIT
