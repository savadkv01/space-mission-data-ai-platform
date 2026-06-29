# Prompt Consistency Review

## Scope

Reviewed:

- [.github/copilot-instructions.md](./copilot-instructions.md)
- [.github/prompts/_shared.prompt.md](./prompts/_shared.prompt.md)
- All phase prompt files in [.github/prompts](./prompts/)

## Summary

I found 4 material issues:

1. Two high-severity internal contradictions in Phase 11 and Phase 12.
2. One medium-severity incident-management gap that will make cross-phase consolidation inconsistent.
3. One medium-severity consistency gap between global/shared rules and several early-phase prompt deliverables.

## Findings

### 1. High: Phase 11 mixes design-only instructions with implementation-only rules

Relevant lines:

- [Phase 11 objective says planning only](./prompts/11-serving-layer.prompt.md#L31)
- [Phase 11 explicitly forbids code implementation](./prompts/11-serving-layer.prompt.md#L33)
- [Phase 11 critical rules require implementation](./prompts/11-serving-layer.prompt.md#L39)
- [Phase 11 critical rules require tests](./prompts/11-serving-layer.prompt.md#L41)
- [Phase 11 deliverables are documentation-only](./prompts/11-serving-layer.prompt.md#L370)
- [Phase 11 definition of done is design-oriented](./prompts/11-serving-layer.prompt.md#L456)

Why this is a problem:

- The prompt says not to implement code, then immediately says this is an implementation phase.
- The required outputs are markdown documents, not runnable assets.
- A strict executor cannot satisfy both the objective and the critical rules at the same time.

Suggested fix:

- Choose one mode and align the whole prompt to it.
- Recommended: make Phase 11 a design phase, because its deliverables and definition of done already read like architecture documentation.
- If that is the intent, replace the implementation rule with language such as: "Design serving tables, materialized views, and data products; do not build SQL/dbt artifacts in this phase."
- If implementation is actually intended, then the prompt needs real code/config deliverables and acceptance criteria for runnable assets.

### 2. High: Phase 12 has the same design-vs-implementation contradiction

Relevant lines:

- [Phase 12 says it is architecture and implementation planning](./prompts/12-bi.prompt.md#L22)
- [Phase 12 forbids dashboard implementation and SQL](./prompts/12-bi.prompt.md#L24)
- [Phase 12 critical rules require dashboard implementation](./prompts/12-bi.prompt.md#L30)
- [Phase 12 critical rules require dataset SQL and dashboard export artifacts](./prompts/12-bi.prompt.md#L31)
- [Phase 12 deliverables are documentation-only](./prompts/12-bi.prompt.md#L301)
- [Phase 12 definition of done is design-oriented](./prompts/12-bi.prompt.md#L372)

Why this is a problem:

- The prompt prohibits the exact activities its critical rules require.
- The deliverables do not provide a place for the required SQL or assets-as-code outputs.
- This will produce inconsistent behavior depending on whether the executor prioritizes the objective, the critical rules, or the deliverables section.

Suggested fix:

- Choose one mode and align title, objective, critical rules, deliverables, acceptance criteria, and definition of done.
- Recommended: keep Phase 12 as a design phase and remove implementation-only language.
- If implementation is intended instead, update the deliverables to include actual Superset assets and dataset SQL locations.

### 3. Medium: Incident requirements are repeated across phases, but there is no shared incident template or precise consolidation scope

Relevant lines:

- [Phase 10 requires 10 production incidents](./prompts/10-data-quality.prompt.md#L287)
- [Phase 11 requires 10 realistic incidents](./prompts/11-serving-layer.prompt.md#L320)
- [Phase 13 requires 10 production incidents](./prompts/13-feature-store.prompt.md#L40)
- [Phase 20 says to consolidate incidents from all phases](./prompts/20-production-incidents.prompt.md#L15)
- [.github/prompts/_shared.prompt.md](./prompts/_shared.prompt.md)

Why this is a problem:

- Many prompts require incident scenarios, but there is no shared schema for how those incidents should be recorded.
- Phase 20 says "all phases," but incident requirements only appear in a subset of phases, mainly later operational and implementation phases.
- Without a common structure, Phase 20 consolidation will be inconsistent and partly interpretive.

Suggested fix:

- Add a shared incident template to [.github/prompts/_shared.prompt.md](./prompts/_shared.prompt.md) or create a dedicated shared file such as `INCIDENT-TEMPLATE.md`.
- Standardize fields such as `ID`, `phase`, `severity`, `symptoms`, `root cause`, `detection`, `resolution`, `prevention`, `MTTD`, and `MTTR`.
- Reword Phase 20 from "all phases" to "all prior phases that define incident scenarios" or explicitly enumerate the source phases.

### 4. Medium: Shared conventions and README requirements are applied inconsistently across the prompt set

Relevant lines:

- [.github/copilot-instructions.md requires every phase to generate README.md](./copilot-instructions.md#L170)
- [README.md requirement line](./copilot-instructions.md#L172)
- [.github/prompts/_shared.prompt.md says each phase ships a README.md](./prompts/_shared.prompt.md#L21)
- [Later prompts explicitly load shared conventions](./prompts/13-feature-store.prompt.md#L7)
- [Phase 03 deliverables section](./prompts/03-solution-architecture.prompt.md#L297)
- [Phase 06 deliverables section](./prompts/06-data-modeling.prompt.md#L329)
- [Phase 10 deliverables section](./prompts/10-data-quality.prompt.md#L337)
- [Phase 11 deliverables section](./prompts/11-serving-layer.prompt.md#L370)
- [Phase 12 deliverables section](./prompts/12-bi.prompt.md#L301)

Why this is a problem:

- Phases 13-25 explicitly inherit the shared rules, but Phases 01-12 do not.
- Several early prompts have deliverable lists that do not include `README.md`, even though both the global instructions and shared conventions say every phase should ship one.
- That inconsistency will lead to uneven documentation structure across phases.

Suggested fix:

- Add `Read .github/prompts/_shared.prompt.md first` to Phases 01-12, or explicitly inline the shared rules there if that split is intentional.
- Align the deliverables for Phases 02-12 with the global `README.md` requirement.
- If early phases are intentionally exempt, relax the global/shared rule so the expectation is not universal.

## Optional Improvement

### 5. Low: Phase 2 and Phase 5 overlap on dataset discovery scope

Relevant lines:

- [Phase 2 requires identifying at least 25 datasets/APIs](./prompts/02-domain-research.prompt.md#L88)
- [Phase 5 says it analyzes all data sources identified in Phase 2](./prompts/05-source-data-analysis.prompt.md#L18)
- [Phase 5 re-opens dataset inventory expansion](./prompts/05-source-data-analysis.prompt.md#L61)
- [Phase 5 raises the target to 30-50 datasets/APIs in total](./prompts/05-source-data-analysis.prompt.md#L67)

Why this is a problem:

- This is not a hard contradiction, but it weakens the phase boundary.
- A strict executor may redo discovery work instead of moving from breadth-first research to depth-first profiling.

Suggested fix:

- Clarify that Phase 2 is breadth-first discovery and prioritization.
- Clarify that Phase 5 is deep technical profiling of the selected Phase 2 inventory, with optional additions only when justified.

## Recommended Priority Order

1. Fix Phase 11.
2. Fix Phase 12.
3. Standardize incident documentation before relying on Phase 20 consolidation.
4. Align Phases 01-12 with shared/global conventions.