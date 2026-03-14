# Canon Reconciliation Report

**Date:** 2026-03-13  
**Input:** Recovered Galactic Union core packet derived from `intake/textAu.txt` and normalized against current GUMAS engine traces  
**Layer:** L2  
**Entities processed:** 16  
**Reconciler version:** aurora-canon-reconciler v1.0

---

## Validation Summary

| Entity | Layer | Type | Status | Issues |
|--------|-------|------|--------|--------|
| Galactic Union | L2 | polity | PASS | 0 |
| Prime Construct Polity | L2 | polity | PASS | 0 |
| Separatist Confederation | L2 | polity | PASS | 0 |
| PMC Syndicate | L2 | polity | PASS | 0 |
| Velar Imperium | L2 | polity | PASS | 0 |
| Crimson Pact | L2 | polity | PASS | 0 |
| Chancellor Zylox Rhaegos | L2 | character | PASS | 0 |
| General Kael Durn | L2 | character | PASS | 0 |
| Grand Strategist Lirian Vael-Torin | L2 | character | PASS | 0 |
| Director Varek Norr | L2 | character | PASS | 0 |
| Chief Marshal Vael Saros | L2 | character | PASS | 0 |
| High Chancellor Renn Valcor | L2 | character | PASS | 0 |
| Admiral Selene Arcturus | L2 | character | PASS | 0 |
| Director Callan Deyrus | L2 | character | PASS | 0 |
| Minister Anaya Ral-Seyr | L2 | character | PASS | 0 |
| Prime Construct | L2 | character | PASS | 0 |

Validation receipt id:

- Combined validation run receipt: `299830edbd2a7b4022e21cfec382ecd57873713147681559dc15952ed60bbbb7`

---

## Conflicts Found

No direct contradictions were identified inside the scoped promotion packet.

Scope note:

- this report is based on the recovered-source reconciliation and the engine-name normalization pass already performed
- the packet was first validated with `--no-context-scan` and then re-checked with a broader context scan rooted at `GUMAS_SIM_2.5`
- the context-aware scan produced no blocks and only one expected alias-overlap warning around `Prime Construct`

---

## Drift Artifacts

- **Name normalization** in `canonical_name`: `Chancellor Zylox` was normalized to `Chancellor Zylox Rhaegos`
- **Name normalization** in `canonical_name`: `Grand Strategist Lirian Vos` was normalized to `Grand Strategist Lirian Vael-Torin`
- **Faction normalization** in `canonical_name`: `Separatist Movements` was normalized to `Separatist Confederation`
- **Faction normalization** in `canonical_name`: `Corporate PMCs` was normalized to `PMC Syndicate`
- **Exclusion gate** in `scope`: the hostile AI hardliner placeholder and `Judicator Prime` cluster were kept out of this packet to avoid mixing corroborated and draft-only material

---

## Promotion Assessment

| Entity | Current Tag | Proposed Tag | Reasoning |
|--------|-------------|-------------|-----------|
| Galactic Union | CANON_PROMOTE | CANON_PROMOTE | Clean schema validation, strong recovered provenance, and centrality to the Union core |
| Prime Construct Polity | CANON_PROMOTE | CANON_PROMOTE | Recovered AI sovereignty split survived into later engine traces |
| Separatist Confederation | CANON_PROMOTE | CANON_PROMOTE | Stable faction normalization across recovered and engine references |
| PMC Syndicate | CANON_PROMOTE | CANON_PROMOTE | Core political-economic bloc repeatedly present in the recovered material |
| Velar Imperium | CANON_PROMOTE | CANON_PROMOTE | Strong faction anchor with durable recovered profile |
| Crimson Pact | CANON_PROMOTE | CANON_PROMOTE | Persistent faction slot with coherent recovered identity |
| Chancellor Zylox Rhaegos | CANON_PROMOTE | CANON_PROMOTE | Central leader with recovered-to-engine name normalization completed |
| General Kael Durn | CANON_PROMOTE | CANON_PROMOTE | Strongly corroborated Union leadership figure |
| Grand Strategist Lirian Vael-Torin | CANON_PROMOTE | CANON_PROMOTE | Advisor role clearly survives recovered-to-engine transition |
| Director Varek Norr | CANON_PROMOTE | CANON_PROMOTE | Stable diplomacy-role continuity |
| Chief Marshal Vael Saros | CANON_PROMOTE | CANON_PROMOTE | Central to recovered anti-coup and Marshal expansion logic |
| High Chancellor Renn Valcor | CANON_PROMOTE | CANON_PROMOTE | Duplicate recovery cleaned and stabilized into one dossier |
| Admiral Selene Arcturus | CANON_PROMOTE | CANON_PROMOTE | Strong naval leadership continuity |
| Director Callan Deyrus | CANON_PROMOTE | CANON_PROMOTE | Stable intelligence-role continuity |
| Minister Anaya Ral-Seyr | CANON_PROMOTE | CANON_PROMOTE | Strong economic-governance linkage in recovered material |
| Prime Construct | CANON_PROMOTE | CANON_PROMOTE | Character-level sovereign AI counterpart to the polity dossier |

Advisor note:

- `recommendations.json` recommends `CANON_PROMOTE` for all 16 entities in this packet
- advisor confidence remains low by heuristic-gap scoring (`0.24`) even though schema validation passed, so final human review is still appropriate

---

## Evidence Receipts

- Evidence receipt verdict: `PASS`
- Evidence receipt id: `f036c881a01378abb4cddc474bcc05e94512801f9174ed14e1237b6047a9cbbc`
- Receipt file: `evidence_receipt.json`
- Context-scan evidence receipt verdict: `PASS`
- Context-scan evidence receipt id: `bf542e62426ac750cd3c87c70b65f6149001cdb72b9d2af449b02d8340108093`
- Context-scan validation receipt id: `96ed9bd4990d3aae43a262bd08d9718af06397db07782ab4c1bde4dd9b90c5d3`

---

## Action Items

1. **HIGH** — Human reviewer should approve or narrow the `CANON_PROMOTE` packet before commit.
2. **MEDIUM** — Keep `Judicator Prime`, the draft ship crew cluster, and the AI-hardliner placeholder in staging until corroborated by more sources.
3. **MEDIUM** — Resolve the current validator mismatch for L2 mechanics before promoting mechanic dossiers.
4. **LOW** — If this packet is committed, update downstream faction and roster registries to point at the new canonical IDs.

Reviewer confirmation:

- `Prime Construct` as a canonical name overlap is accepted for this packet.

---

*Generated for the recovered `textAu` promotion workflow. Human review required before any Git commit locks these entities as `CANON`.*
