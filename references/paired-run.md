# Paired run with ecommerce-cia — what runs once and what runs twice when the user names both skills

> Job of this file: loaded only when one request names both /cia and /ecommerce-cia (SKILL.md §0.14); says which skill is the spine, which steps fold into which, and what each contributes once. Section numbers (§0.x) refer to SKILL.md.

Runs only when the user names both skills in one request ("run /cia and /ecommerce-cia", "both auditors", "full audit with both"). Neither skill auto-loads the other (§0.2). When paired, the two overlap almost entirely — same theory, same map, same S1–S24 numbering, same protocol steps — so the paired run does the shared work **once** and the disjoint work **both**:

1. **On a commerce project, `ecommerce-cia`'s §0.6 is the spine** — its seven steps are a superset of this skill's six (it adds the sandbox gateway walk, host-capability reconciliation and the detector roll call as protocol steps). This skill's steps fold in: Step 1 → its Step 1; Step 2 → its Step 3; Step 3 → its Step 4; Step 4 → its Step 5 (contribute any non-web smoke commands for CLI / service parts); Step 5 → the §0.8 fix-vs-ask pass; Step 6 → its Step 7. Do not re-run discovery, the fast suite, the full suite, the runtime walk or the map.
2. **This skill contributes what the sibling does not have:** the extra §0.5 bindings (analyser / linter / dependency-audit configs, CI workflow file, fast-suite filter); its `references/sweeps/` as the *universal* text of every sweep, read alongside the commerce text so each sweep runs once with the union of both texts' checks and emits one report line tagged `S<n> [cia + ecommerce-cia]`; §0.10 AI / LLM boundary sweeps when AI components are found; §3 context profiling with a matching context template; §7 universal test matrix on the non-commerce critical flows; §8 domain checklist. A finding both texts would raise is filed once, under the invariant of the more specific text.
3. **One register, one ID sequence, one report,** in the sibling's Step 7 format, with lines added for this skill's §3 profile, §7 matrix, §8 checklist and §0.10 sweeps. One depth tier, declared once, binds both.
4. **Paired on a non-commerce project** (the user asked for both anyway): this skill's §0.6 is the spine; `ecommerce-cia`'s §0.5 discovery reports that no payment integration, commerce schema or checkout route exists; its commerce sweep text adds no sites; say so in one line and run this skill's protocol.

---

**Reading receipt: _two auditors, one spine_.** Quote this phrase on the report's receipts line (Step 6) to show this file was read rather than inferred from the skill's index.
It appears nowhere else.
