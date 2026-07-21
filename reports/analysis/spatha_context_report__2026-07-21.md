# The Spatha Moderna — Context Recovery Report — 2026-07-21

**Purpose:** consolidate everything established about the Marshal sword (Spatha Moderna /
"spade") across the workspace, identify why canon context feels thin, and queue the gaps.
**Finding in one line:** the spatha has a rich, owner-locked design history in a mined
archive thread (2026-02-01/02) and an L2 sim capture, but **only one line of it ever
landed in canon** — the rest never left the raw archive.

## 1. What canon currently says (the entire record)

`CanonRec canon/L2/operations/Marshal_Standard_Kit.md` (and two stale copies):

> **Spatha Moderna** (formal) — commonly called *spade*

That is the complete canonical record. The word "spatha" appears nowhere else in CanonRec —
not in the marshals ledger, the Archive Mining Addendum, the Marshal Charter, or the
mechanics registry.

## 2. Recovered context — the design thread (raw archive, 2026-02-01/02)

Source: `archives/unzipped/ZIP_Archives/9c9ce296…/conversations.json` (22 distinct
spatha-bearing messages). This thread contains explicit **"canon locked"** declarations
by the owner that were never promoted:

### 2.1 Identity & naming (owner-locked in thread)
- **Formal designation:** *Spatha Moderna* (plural *spathae* in formal registers).
  "Moderna" = *current, adapted, fit for present conditions* — not futuristic; follows real
  historical variant-naming patterns (*gladius hispaniensis*, *usus modernus*).
- **Three-layer naming structure:** formal/doctrinal *Spatha Moderna* → Marshal internal
  shorthand *spade* → civilian/frontier speech *spade*, "Marshal blade", "that thing they carry".
- **Etymological rationale:** spatha → *spada/espada/épée/spade*; "the frontier didn't
  invent a nickname; it inherited one."
- **Historical anchor:** the Roman spatha — longer one-handed sword, shield-compatible,
  institutional/issued, "a reach extension for authority operating in less controlled
  spaces… that's frontier logic."
- Pronunciation note recorded: SPA-thuh (/ˈspæ.θə/), with expected frontier
  dialect drift ("spather", "spath", "spade").

### 2.2 Physical description (thread-locked, absent from canon)
- Spatha-derived, **slightly curved** (frontier evolution), **single-edge dominant**,
  **strong thrusting point**
- Powered blade; modern materials and power integration
- One-handed; designed for **shielded advance**; longer than a gladius
- **Carried daily as a marker of office** — "worn, not brandished"

### 2.3 Doctrine & cultural register (thread-locked)
- Class: "Marshal close-engagement authority blade"; recognized symbol of Marshal
  authority across the frontier
- "Diplomacy-first, lethal-when-drawn": Marshals seek diplomatic solutions, but **once
  swords are drawn they commit** (confirmed in the 2026-02-03 hard-reset sweep as
  explicitly established, not inference)
- Usage idioms locked: "Secure your spade" / "If the spades come out, it's over" /
  "He didn't draw the spade—went straight to iron"
- Kit linguistic asymmetry (deliberate): only the anomalous tool (sword) gets a distinct
  name — *Spade* (Spatha Moderna), *Iron* (MR-6 revolver), *Viper* (MFR-9 rifle);
  "Spade and Viper" as frontier shorthand

## 3. Recovered context — L2 sim capture (Frontier Enforcement Escalation Study)

Source: `projects/GUMAS_SIM_2.0/02_DEVELOPMENT/…/l_2_sim_capture_marshals_ranger_sentinel_thread_v_1_0.md`
(§4 "Sword", observed-use-only; §9 states all contents were **promoted to canon by L1**):

- Powered blade weapon; geometry supports **slashing, lopping, and thrusting**
- Employed with a **one-handed shield** during close-quarters engagements
- Serves as combat implement **and** visible marker of Marshal authority
- Pair tactics context: alternating pressure, controlled advances under shield (Cross &
  Vorn operating as a synchronized pair)

## 4. Provenance chain (how the spatha came to exist)

1. **DuelSim historical-fencing research** (`GUMAS_SIM_2.5/DuelSim/archive/research_docs/`,
   2026-02-21 scaffold; Roman section lists the real spatha) — the real-world research
   track that fed the design instinct.
2. **Design thread, 2026-02-01/02** (raw archive): gladius vs spatha analysis → name lock
   → *Spatha Moderna* full-formal lock → kit canvas v1.0 → Viper folded in (v1.1).
3. **Marshal_Standard_Kit.md** — the one-line distillation that became the canon file.
4. **L2 sim capture** — observed use; L1-promoted per its §9.
5. **Union Marshals dossier (2026-07-20)** — cites the kit line + capture, adds nothing new.

## 5. Gap analysis (why context "feels missing" — it is)

| # | Gap | Severity | Detail |
|---|---|---|---|
| G1 | **Design canon never promoted** | HIGH | All §2 content (naming structure, physical description, doctrine, idioms) exists only in the raw archive. The 2026-07-21 corpus audit's "fully mined" verdict covered *extraction*, not *promotion* — this thread was mined for Marshals org structure, and the spatha material was left behind. |
| G2 | **Sim capture not in CanonRec** | HIGH | The capture declares L1 canon promotion (§9) but lives only under `projects/GUMAS_SIM_2.0`; CanonRec has no copy and no receipt. Unverifiable promotion claim — contra "evidence over assumption". |
| G3 | **Cross & Vorn unrecorded** | MEDIUM | Named actors in a canon-promoted capture with zero entity records — a **C4 roster-closure** violation-in-waiting the moment the capture's promotion claim is honored. Vorn's Bracer device likewise unrecorded. |
| G4 | **Kit file duplication drift** | MEDIUM | Three copies: `canon/L2/operations/` (current — includes 2026-07-21 Ranger drone ruling), `canon/L2/marshals_sentinels/` and `projects/…/SimLogsBuild/` (both stale, pre-drone). The marshals dossier cites the operations path; the stale sibling inside canon/ invites contradiction. |
| G5 | **No equipment-class record** | LOW | No entity/mechanics record exists for the Spatha Moderna itself (or MR-6/MFR-9). The mechanics registry has no weapons section. Whether kit items warrant entity records is an owner scope call. |

## 6. Recommended actions (owner rulings / queue candidates)

1. **Promote the spatha design canon** (G1): fold §2 into a proper record — either a
   `SPATHA_MODERNA` section in the marshals ledger or a kit-detail file beside
   `Marshal_Standard_Kit.md` — via aurora-canon-reconciler with the archive thread as
   source. The thread's "canon locked" statements are owner declarations; promotion is
   ratification, not invention.
2. **Land the sim capture** (G2): copy into CanonRec (e.g. `canon/L2/operations/` or
   `marshals_sentinels/`) with a promotion receipt, or formally demote its §9 claim.
3. **Roster ruling for Cross & Vorn** (G3): create entity records (Aric Thal precedent:
   documented source = the capture + design thread) or rule them sim-ephemeral.
4. **Deduplicate the kit** (G4): declare `canon/L2/operations/Marshal_Standard_Kit.md`
   canonical; SUPERSEDE or delete the `marshals_sentinels/` copy (alias-forward precedent).
5. Optional (G5): equipment-class records for Spade/Iron/Viper if kit items should be
   linter-checkable entities.

## 7. Source register

- Raw design thread: `archives/unzipped/ZIP_Archives/9c9ce296…22da4e485f0b487cae0716c77b02b379/conversations.json` (msgs 2026-02-01 19:23 → 2026-02-03 02:36)
- Sim capture: `projects/GUMAS_SIM_2.0/02_DEVELOPMENT/Project_Main/Project_Files_GUMAS2_0/l_2_sim_capture_marshals_ranger_sentinel_thread_v_1_0.md`
- Canon kit: `GUMAS_SIM_2.5/CanonRec/canon/L2/operations/Marshal_Standard_Kit.md` (+ 2 stale copies)
- DuelSim research: `GUMAS_SIM_2.5/DuelSim/archive/research_docs/For a sub project, I am researching historical fen.md`
- Dossier: `reports/analysis/union_marshals_dossier__2026-07-20.md`
