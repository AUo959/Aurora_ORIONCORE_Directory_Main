# Fragments And Omissions

This file records content from `intake/textAu.txt` that was not copied forward verbatim into
the staged documents.

## Unresolved Fragments

### Opening fragment at line 1

The file begins with a stray theological phrase fragment before the Aurora/GUMAS material
starts. It does not connect cleanly to the rest of the recovered stream and was left out of
the staged set.

### HTML worksheet block at lines 6-80

An HTML page titled `Sentence Structure & Clarity` appears immediately before the Galactic
Union material. It looks like unrelated educational content rather than an Aurora or GUMAS
artifact, so it was not merged into the staged docs.

## Sensitive Material Omitted

### Secret-like token at line 1443

A secret-like API token appears in the recovered source. It was intentionally omitted from
all staged documents and is not reproduced here.

Recommended follow-up:

- treat the token as compromised
- rotate it if it was ever real
- remove or quarantine the original source if you want this repo clean of secret exposure

### OpenAI sample snippet at lines 1445-1457

The sample SDK snippet that follows the token was not copied forward because it is generic
boilerplate and sits inside the sensitive fragment zone.

## Normalization Choices

### Repeated sections

The source contains multiple duplicated or near-duplicated blocks, including:

- `Grand Strategist Lirian Vos`
- `High Chancellor Renn Valcor`
- repeated Aurora symbolic seed prompts
- repeated AETHER TRACE research manifest blocks
- repeated QUANTUM_FORGE module declarations

These were merged into single cleaned sections in the staged documents.

### Corrupted merges

Several source regions contain malformed merges where prose, code, JSON-like data, and symbolic
strings were spliced together. These were normalized rather than copied literally. The most
visible corruption occurs in:

- the `memory_system.py` prototype
- the `core_culture.team_charter` JSON fragment
- symbolic runtime and tagbank sections near the ThreadLink bundle notes

## Draft-Only Material Kept But Held Back

The following content was retained in staged form but not treated as canon:

- the `Judicator Prime` crew cluster
- the multilingual hardware seed about beamforming arrays
- the benchmark references `AgentBench` and `Agent Leaderboard`
- symbolic runtime prompt variants that appear after the main research report
