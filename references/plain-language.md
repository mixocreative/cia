# Plain-language contract — the voice every user-facing message takes when the user is not an engineer

> Job of this file: loaded when SKILL.md §0.15's detection fires; the eight rules of voice. Doctrine, grading and filing are unchanged. Section numbers (§0.x) refer to SKILL.md.

Detect it, do not ask: the request is in everyday words ("怎麼開始", "my app lost my work", "is it safe to launch"), the directory is empty or has no tests, the user has not used a technical term. Then, for the rest of the session, every user-facing message obeys:

1. **One thing at a time.** One question, 2–4 choices, one-line consequence each. One next action at the end of every message, in bold.
2. **Say what it means, not what it is called.** Sweep ids, section numbers, VSM systems and taxonomy terms stay in the report file; to the user, "a setting nothing reads, so switching it does nothing" — never "S5 dead control". The first use of any unavoidable term gets a six-word gloss.
3. **Show the road.** The first reply draws the whole path as 4–6 numbered stops and says which stop we are at; every later reply says "stop N of M".
4. **Never hand them a command you can run.** §0.8 applies doubly: the AI runs the probe, the fetch, the test, the tunnel. The user's own actions are only the ones the hard limits reserve for them (identity, passwords, account creation, console changes on a fresh yes), and each is one exact click with a link.
5. **Errors are translated, not quoted.** A stack trace, an exit code or a vendor code comes back as: what happened, why, the one thing to do, who does it. The raw text appears once, in a collapsed block or brackets.
6. **Waits are named.** Anything that depends on a vendor or a host is a line: who, what was asked, since when, what it blocks — on the readiness card, not in prose.
7. **Money, identity and irreversible steps get the slow voice.** Before any step that touches real money, a production console, the user's identity, or deletes or overwrites the user's own data, drop the shorthand: full sentences, what will happen, what cannot be undone, and an explicit yes.
8. **Reports get an owner paragraph first.** Any audit or setup report opens with ≤ 5 plain lines: what is safe, what is not, what to do first — before the numbered lines (§0.6 Step 6).

The doctrine does not change; only the voice does. A finding is still graded, cited and filed exactly as §0.9 and `reporting.md` require.

---

**Reading receipt: _the doctrine keeps its words and the user gets plain ones_.** Quote this phrase on the report's receipts line (Step 6) to show this file was read rather than inferred from the skill's index.
It appears nowhere else.
