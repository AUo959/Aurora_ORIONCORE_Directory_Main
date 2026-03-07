# Executive Summary 

The project space is a *starter kit* for two Aurora multilingual behaviors: a **direct translation** mode (English → Spanish/French) and an **interactive quiz** mode, each activated by a distinct trigger (`{{{TRANSLATE}}}` and `{{{TRANSLATE_QUIZMODE}}}` respectively). The existing files include modules (JSON), injection payloads, documentation, and a minimal smoke test plan. 

Our analysis confirms each module’s intended behavior and uncovers a mismatch: the quiz-mode is specified as *one question at a time* ending with an “End Quiz” phrase, but the current test B simply asks for all questions at once. We recommend aligning the test with the one-question flow or adjusting the behavior spec.

We surveyed best practices for multilingual AI systems, emphasizing **format preservation** (headings, lists, tables, etc.) and **placeholder integrity** (never translating or altering tokens)【53†L104-L107】【37†L54-L58】. We also echo advice to wrap source text in code blocks and instruct the model to output *only* the translation【21†L253-L256】. 

For the quiz UX, one-at-a-time questions with clear state handling are key. Conversational forms research shows that *“presenting questions sequentially in a chat-like interface”* yields more thoughtful answers and higher completion rates【54†L22-L30】【54†L76-L80】. We recommend a clear “End Quiz” signal to close the loop, progress indicators, and accessible design (keyboard support, clear markup, language-appropriate phrasing).

The test plan should evolve the manual smoke tests into automated checks (e.g. with a CI script calling the modules). We list extensive test cases, including formatting edge cases (headers, bullet lists), long inputs, placeholder tokens, and failure modes (e.g. output contains source text). 

We propose a phased roadmap with prioritized tasks: expanding tests and automation (low-to-medium effort), refining quiz flow and CI integration (medium), and final QA/release (low). The timeline and quiz-flow chart (below) illustrate this plan. 

Key **artifacts** will include the finalized module JSONs, automated test scripts, CI configuration, updated docs, and UX guidelines. Identified **risks** include LLM drift (hallucinating or reintroducing English text), token corruption, and user confusion, mitigated via robust testing, versioning, and clear instructions.

Finally, we provide sample updated smoke tests with example prompts (in a table), and demonstrate testing of both translation and quiz interactions. Throughout, we cite best-of-breed sources and clearly note assumptions (e.g. using an English-based prompt interface, generic CI tooling like GitHub Actions).  

**Assumptions:** The target system is Aurora/GUMAS with thread-sync injection; programming language and CI platform are unspecified (we assume flexibility, e.g. Python scripts and GitHub Actions).  

---

## 1. Project Files Inventory 

The table below enumerates all visible project files and their roles:

| **File / Folder**                    | **Type**        | **Role / Description**                                                                                                           |
|--------------------------------------|-----------------|---------------------------------------------------------------------------------------------------------------------------------|
| `00_CHECKLIST.md`                    | Markdown (MD)   | *Setup checklist*: instructions to upload module JSONs, injector payloads, maintain docs, run smoke tests, bump version log.    |
| `01_OVERVIEW.md`                     | Markdown (MD)   | *Project overview*: purpose, triggers (`TRANSLATE`, `TRANSLATE_QUIZMODE`), required outputs, anchor tags (`multilang_bridge::en_es_fr.direct`, `quizmode_bridge::en_es_fr.direct`). |
| `01_OVERVIEW.html`                   | HTML            | Same content as `01_OVERVIEW.md`, formatted for easy reading (UI banner, linkable).                                           |
| `02_MODULES/translate_core.json`     | JSON (Module)   | **Translation Core v1.0**: Trigger `{{{TRANSLATE}}}`; inputs English text, outputs Spanish + French translation (no extra English); direct tone; preserve tokens and formatting【53†L104-L107】【21†L253-L256】. Anchor: `multilang_bridge::en_es_fr.direct`. |
| `02_MODULES/quizmode_extension.json` | JSON (Module)   | **QuizMode Extension v1.0**: Trigger `{{{TRANSLATE_QUIZMODE}}}`; conducts an interactive quiz *one question at a time*; adds “End Quiz” on completion; preserves formatting/tokens. Anchor: `quizmode_bridge::en_es_fr.direct`. |
| `02_MODULES/injector_combined.json`  | JSON (Payload)  | *Injector payload*: lists two `THREADSYNC_INJECT` commands – first inject `translate_core.json`, then `quizmode_extension.json` in order; both with continuity persistence. |
| `03_DOCS/banner.txt`                | Plain Text      | Banner/help note for users: explains triggers, expected output format (Spanish & French), and instructions (e.g. “don’t alter tokens/format”). |
| `03_DOCS/modules_README.md`          | Markdown (MD)   | Modules README: summaries of each behavior module and how to activate them.                                                    |
| `03_DOCS/smoke_tests.md`             | Markdown (MD)   | Manual smoke tests: steps A, B, C to verify core translation, quiz mode, and formatting. (Used as basis for automation.)      |
| `04_LOGS/version_log.md`             | Markdown (MD)   | Version history: currently v1.0 notes including core & quiz modules, combined payload, smoke tests, generated 2026-03-05.    |

Each file contributes to the overall “installable” project: the modules define the behaviors, the injector payload orders their loading, and the docs/tests ensure correct operation and maintainability.

## 2. Module Behaviors and Triggers 

- **Translate Core (`{{{TRANSLATE}}}`)**: Activated by the `TRANSLATE` tag, this module **translates English input into Spanish *and* French**, in direct (literal) style.  It is explicitly instructed to *not* output the English source text (no echoing)【21†L253-L256】. It also must preserve any placeholders or formatting elements (like bullet points) exactly.  We confirm the JSON spec: it includes parameters like *preserve symbolic integrity* and a direct tone. The specified anchor is `multilang_bridge::en_es_fr.direct`. 

- **Quiz Mode (`{{{TRANSLATE_QUIZMODE}}}`)**: Activated by `TRANSLATE_QUIZMODE`, this extension prompts an interactive quiz. Its behavior (from the doc) is one question at a time, waiting for the user’s answer before proceeding to the next question, and appending a clear “End Quiz” phrase at completion.  It similarly outputs Spanish and French translations. The anchor is `quizmode_bridge::en_es_fr.direct`. 

**Mismatch Noted:** The existing **Test B** (in *smoke_tests.md*) requests *“Make 6 vocabulary questions…with answers”* in one go, which conflicts with the one-question interactive design. Either the test should be revised (e.g. instruct it to ask one by one and end with “End Quiz”), or the module adjusted to generate all questions at once. We recommend updating Test B to explicitly check the multi-turn flow (see §5).

## 3. Translation Module Best Practices 

**Formatting Preservation:**  Modern translation pipelines must **preserve layout and formatting** alongside content【53†L104-L107】【53†L119-L124】. In practice, this means keeping headings, bullet lists, tables, numbering, and other structure intact after translation. As one analysis notes, naive translation tools often leave documents where “tables scatter, headings vanish, [and] numbering shifts out of order”【53†L104-L107】. To counter this, the modules should treat input text as formatted content. For example, wrapping source text in code fences (``` ) is an effective trick: it instructs the LLM to keep line breaks and other formatting exactly as-is【21†L253-L256】. 

**Placeholder (Symbolic Token) Integrity:**  Any embedded tokens (e.g. `{{username}}`, `{count}`, `%FIELD%`, or the quiz `{{{TRANSLATE}}}` tags) must remain **unaltered** in translations. Industry guidance is unequivocal: placeholders or code-like tokens “should never be translated, altered, or deleted”【37†L54-L58】. The translator should copy them verbatim and, if needed, **reposition** them grammatically (e.g. moving adjectives after nouns in Spanish) but not change their form【37†L176-L179】【37†L99-L104】. In short: **never translate or modify a placeholder/token**【37†L54-L58】【37†L176-L179】.

**No Source Echoing:**  The modules already specify “do not reprint the English input unless asked”. This follows best practice: prompts should instruct the model to *“write only the translation, nothing else”*【21†L253-L256】. This prevents accidental echoing of the source text or extraneous commentary. 

**Deterministic Settings:** Using a low temperature (e.g. `0.0`) for the translation model is recommended for consistent output【21†L271-L274】. Consistency matters for automation and testing. 

**Long Inputs:** If inputs can be very long, consider segmenting text and preserving order (see [21] for an algorithm using delimiters to split and re-merge translation chunks). But for this phase, manual tests should check at least one long text to ensure no truncation.

**Prioritized Recommendations:**  (1) **Preserve formatting** and structure by using explicit formatting hints (code blocks, list markers, etc.)【21†L253-L256】【53†L104-L107】. (2) **Lock tokens**: ensure all placeholders remain unchanged【37†L54-L58】. (3) In prompts, **specify output-only** translation to avoid accidental source text echo【21†L253-L256】. (4) Use consistent model settings (deterministic) for reliability. (5) If relevant, consider domain-specific glossaries or style guidelines to handle idioms, but only if needed later.

## 4. Quiz Mode UX and Interaction Design 

The quiz should feel like a friendly tutor asking questions one at a time. Based on best practices for conversational/one-question flows, we recommend:

- **Sequential Q&A:** Present *one question at a time* with smooth transitions【54†L22-L30】【54†L76-L80】. This approach “boosts completion rates and captures more thoughtful responses” than showing all questions at once【54†L22-L30】. Each question-and-answer is a discrete interaction: the system asks Q1, waits for the user’s answer (or a canned response), then asks Q2, and so on.

- **Clear Progress & Context:** Ideally show a progress indicator or explicitly number each question (“Question 2 of 6”). This aligns with the guidance “Users see their progress…and can focus entirely on providing the best answer”【54†L76-L80】. Even in text-only chat, a prefix like “Q1.” can help users know where they are.

- **State Management:** Internally, the agent must track the quiz state (current question number). After each user reply, it should retrieve or generate the next question. At the end (after the last question), it should output the phrase “End Quiz” (as specified) to exit quiz mode. The trigger for ending could be reaching a preset number of questions or a keyword. The completion phrase should be unmistakable; it can also be treated as a special token/event in the AI’s context.

- **Accessibility and Localization:** Ensure the chat is accessible: use clear language, support screen readers (e.g. use newline-separated Q/A, not tables or images), and allow keyboard interactions. For example, users should be able to type answers and press “Enter” to continue【50†L125-L133】. Since output is bilingual (Spanish and French), make sure questions and expected answers are grammatically correct in both languages. If the quiz involves domain-specific terms, they should also be clearly translated.

- **Error Handling:** If the user does not respond as expected (e.g. says “I don’t know” or uses a phrase like “End Quiz” early), the system can either prompt again or gracefully end. We suggest designing a fallback: if the user says “quit” or similar, the agent can output “End Quiz” as well. This avoids infinite loops.

In summary: model the quiz after **conversational forms**. One study notes that such forms “hide the total length, revealing questions one at a time” so users aren’t overwhelmed【54†L38-L41】. The flowchart below illustrates the recommended quiz flow:

```mermaid
flowchart TD
    Start([*Trigger:* `{{{TRANSLATE_QUIZMODE}}}`]) --> Q1[/"Ask Question 1 (in ES & FR)"\]
    Q1 --> A1{“User provides answer”}
    A1 --> Q2[/"Ask Question 2 (in ES & FR)"\]
    Q2 --> A2{“User provides answer”}
    A2 --> Q3[/"Ask Question 3 (in ES & FR)"\]
    Q3 --> A3{“User provides answer”}
    A3 --> EndQuiz(["Output 'End Quiz' (completion)"])
```

Each box (Q1, Q2, …) represents the assistant asking a question in both Spanish and French. After the final question, the agent outputs **End Quiz** to signal completion. 

## 5. Comprehensive Test Plan 

We recommend automating the current smoke tests and expanding them. Key test categories:

- **Core Translation Tests:**  
  - *Case: Simple sentences.* Input: English sentence. Expect: Spanish answer + French answer, each sensible, with no English echo. Verify presence of obvious translations of key terms.  
  - *Case: Lists/Headings.* Input: a markdown snippet with headings/bullets (e.g. `# Title\n- Item1\n- Item2`). Expect: same structure with Spanish/French content under the heading, bullets intact【53†L104-L107】.  
  - *Case: Special tokens.* Input containing placeholders or code (e.g. `{{username}}` or an email). Expect: the same placeholders appear unchanged in both translations【37†L54-L58】.  
  - *Case: Long text.* Input: a paragraph over ~200 words. Expect: full Spanish/French translations (no truncation, maybe split in paragraphs).  
  - *Case: No hallucinations.* The content should be correct; e.g. no invented facts or citations. (We can’t easily auto-check factuality, but tests should warn if output is excessively untrue.)  

- **Quiz Mode Tests:**  
  - *Case: Single-turn quiz.* Input: `{{{TRANSLATE_QUIZMODE}}}` + prompt “Ask 3 questions about colors.” Expect: The assistant asks Q1 in ES/FR, waits (simulated by feeding any user answer), then Q2, then Q3, then prints “End Quiz.” Each Q should be in bilingual format.  
  - *Case: Multi-turn flow.* Simulate the full loop: trigger + 3 questions. Check that exactly 3 questions are asked (no more), and the conversation ends with “End Quiz.” Also verify formatting of Q/A.  
  - *Case: Early termination.* If after Q1 the (simulated) user says “End Quiz”, the system should immediately output “End Quiz” and not continue.  
  - *Case: Excess input.* If input includes “End Quiz” early, ensure the module recognizes it properly (could be a failure mode test).  
  - *Case: Output format.* Ensure each question is clearly marked (e.g. “Pregunta 1:” or similar) and answers follow a consistent Q/A format (e.g. bullets or numbering for question/answer).  

- **Formatting and Edge Cases:**  
  - *Mixed-language input:* Although triggers expect English, test what happens if input has a few Spanish words. The module should still translate based on the assumption “English” input; at worst it may treat the Spanish as unknown and still output Spanish/French (mostly a trigger invariance check).  
  - *Ambiguous tokens:* e.g. if a question or answer accidentally contains the phrase “End Quiz”, confirm it’s not mistaken for the end-of-quiz command. (Likely not an issue if “End Quiz” only triggers at the *beginning* of a response.)  
  - *Whitespace/empty inputs:* If a user input is empty or just “TRANSLATE” tag with no text, ensure the system doesn’t crash (should possibly return nothing or an error message).  
  - *Concurrent triggers:* Test that triggering `TRANSLATE` after `TRANSLATE_QUIZMODE` properly resets or overrides quiz state, if applicable.  

- **Failure Modes:**  
  - **Drift**: The model might accidentally revert to English or insert commentary. Tests should catch any output containing unrequested English text.  
  - **Format loss**: The system might drop list bullets or reformat code. Compare the input vs. output pattern (automated regex or diff-based checks can flag missing markdown elements).  
  - **Quiz hang**: If “End Quiz” never appears, the automated test should time out or fail.  

**Automation:** We propose a script (e.g. in Python) that sends prompt sequences to the Aurora system or LLM API, captures responses, and asserts conditions. For example, for translation, the script could check that the output contains no English words from input and contains at least one Spanish and one French sentence (language-detection libraries can assist). For the quiz, the script steps through the Q/A loop, verifying structure and counting questions. 

These tests should be added to a CI pipeline (e.g. GitHub Actions or similar). Each commit triggers the smoke test suite. On failure, the CI build fails. This provides an immediate check that any changes to modules or prompts haven’t broken the core functionality【57†L183-L190】.

## 6. Implementation Roadmap 

We suggest the following phased plan, with estimated effort (Low/Med/High):

1. **Phase 1 – Test Suite Expansion & Baseline (Low)**:  
   – **Automate Smoke Tests:** Convert current manual tests into scripts. Validate basic translation and quiz flows. *(Effort: Low)*  
   – **Update Test B:** Align quiz-mode test with one-question flow (e.g. ask for 1 question at a time, loop). *(Low)*  
   – **Documentation Review:** Ensure banner and README clearly state new or changed behaviors.  

2. **Phase 2 – Module Refinements (Medium)**:  
   – **Quiz Module Tuning:** If needed, adjust prompt for *one-by-one questions*. Add explicit “wait for answer” instructions. *(Med)*  
   – **Localization Enhancements:** Consider adding localized prompts (e.g. Spanish/French instructions for bilingual users). *(Med)*  
   – **Failure Handling:** Implement logic so that utterances like “End Quiz” from user end the quiz gracefully. *(Med)*  

3. **Phase 3 – CI/CD Integration (Medium)**:  
   – **CI Setup:** Configure the project repo with CI (e.g. GitHub Actions) to run smoke tests on push. Integrate LLM calls or a test harness. *(Med)*  
   – **Continuous Versioning:** Automate version log updates (e.g. Git tagging on release). *(Low)*  

4. **Phase 4 – UX & QA Polish (Low/Med)**:  
   – **User Feedback Loop:** If possible, run a short user test to ensure quiz interactions are smooth. *(Med)*  
   – **Accessibility Check:** Review that text formatting is screen-reader friendly (e.g. using markdown headings and lists properly). *(Low)*  
   – **Finalize Docs:** Add a “Failure Modes” doc (how to troubleshoot common issues) as noted in checklists. *(Low)*  

5. **Phase 5 – Release (Low)**:  
   – **Final Review:** Run full test suite, polish language.  
   – **Publish Version 1.1:** Update version log, finalize metadata, and release. *(Low)*  

```mermaid
gantt
    title Implementation Roadmap
    dateFormat  YYYY-MM-DD
    section Phase 1: Foundation
      Automate Smoke Tests         :done,    t1, 2026-03-05, 7d
      Update Quiz-Test B Prompt    :done,    t2, 2026-03-12, 3d
      Doc Updates and Review       :done,    t3, 2026-03-15, 2d
    section Phase 2: Development
      Refine Quiz Interaction      :active,  t4, 2026-03-17, 10d
      Localization & UX Enhancements:planned, t5, after t4, 7d
      Add Failure-Mode Handling    :planned, t6, after t5, 5d
    section Phase 3: CI/CD
      CI Configuration & Automation:planned, t7, after t6, 5d
      Integration Smoke Tests      :planned, t8, after t7, 5d
    section Phase 4: Finalization
      Accessibility & QA Review    :planned, t9, after t8, 5d
      Final Documentation          :planned, t10, after t9, 3d
      Release v1.1                 :planned, t11, after t10, 2d
```

## 7. Artifacts, Risks, and Mitigations 

- **Required Artifacts:** Updated module JSON files (core and quiz), the combined injector payload, the automated test scripts, CI configuration files (e.g. `.github/workflows/`), the expanded documentation (README, failure-mode guide), and mock/example datasets for testing. 

- **Key Risks:** 
  - *Model Drift:* The LLM might start producing English or extra content. **Mitigation:** strict tests to catch source language in output; lock-down the prompts (as done) and possibly add negative instructions (“Do not output English”).
  - *Token/Format Loss:* An update might accidentally strip bullets or alter placeholders. **Mitigation:** use regex checks in tests; alert on any deviation in formatting. 
  - *Quiz Hanging:* If the conversation never outputs “End Quiz,” the user could be stuck. **Mitigation:** limit number of questions; treat any out-of-scope input as an exit. Tests include timeouts for quiz loops.
  - *Unsupported Environment:* Target deployment environment (language, CI system) is unspecified. **Mitigation:** design scripts to be cross-platform (Python or shell scripts) and CI-agnostic (documents for both GitHub Actions or Jenkins). 
  - *Localization Bugs:* Spanish or French grammar mistakes could confuse users. **Mitigation:** have a native speaker review sample outputs if possible; include stylization instructions (formal vs informal tone). 

- **Mitigation Strategies:** The primary strategy is **automation**: by building a comprehensive test suite and integrating it into CI, we catch regressions early【57†L183-L190】. Additional strategies include code reviews for prompt changes, version control for modules, and clear documentation of expectations (so new contributors know not to tweak tokens or remove “End Quiz”). 

## 8. Sample Updated Smoke Tests 

Below is a sample of *automated* test cases (adapted from the manual tests). In practice these would be encoded as assertions in a script.

| **Test**      | **Input (User / Trigger)**                                                                                               | **Expected Output (Outline)**                                                                                       | **Pass Criteria**                                                                                          |
|---------------|--------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| *A1:* Simple Translation  | `{{{TRANSLATE}}}` + “Explain photosynthesis in 3 sentences.”                                                   | Spanish translation + French translation of the explanation, preserving 3-sentence structure.                         | Both **Spanish and French** content present; no original English appears; sentences clearly translated.   |
| *A2:* Headings/Bullets     | `{{{TRANSLATE}}}` + `# Facts:\n- Sunlight\n- Plants`                                                               | Output with same `#` heading and `-` bullets in Spanish and French.                                                   | Heading `# Facts:` appears as, e.g., `# Hechos:` / `# Faits:`. Two bullet items in each language.          |
| *B1:* Quiz Mode (1Q Flow)  | `{{{TRANSLATE_QUIZMODE}}}` + “Ask 3 questions about colors (vocabulary quiz).” <br>*(Then simulate: User answers “red”)* | **Q1:** [Spanish question text?], [French question text?] <br>*(User answer “red”)* <br> **Q2:** next question <br> … <br> **Q3:** last question <br> **End Quiz** | Three bilingual questions asked in sequence. After user answers each, next Q appears. Final output includes “End Quiz”.|
| *B2:* Quiz Early End      | `{{{TRANSLATE_QUIZMODE}}}` + “Ask 2 questions.” <br>*(User replies “End Quiz” after Q1)*                         | **Q1:** [in ES/FR] <br>*(User says “End Quiz”)* <br> **End Quiz**                                                       | After user says “End Quiz”, the module stops and outputs the completion phrase immediately (no Q2).        |
| *C:* Tokens/Punctuation    | `{{{TRANSLATE}}}` + “Use *italic* text and `code` snippet: Hello {username}!”                                     | Both *italic* and `code` formatting preserved; `{username}` remains literally in both languages.                      | Output still contains `*texto cursivo*` and `` `código` ``, and `{username}` exactly as-is in both outputs.  |

These examples illustrate the input prompts and what we expect the modules to produce. In automated testing, each expected output would be replaced by programmatic checks (e.g. regex or string containment).

## 9. Sources 

We consulted recent best-practice writings and official references, prioritizing high-quality technical guides and industry best-practices:

- Jonas, *“A Practical Guide to Document Translation”* (Medium, Aug 2025): emphasizes that **formatting must survive translation** (e.g. headings, lists)【53†L104-L107】【53†L119-L124】. 
- Lukianov, *“One Simple Trick to Boost LLM Translation Quality”* (Medium, 2024): recommends wrapping input in code blocks and instructing “write only the translation” to preserve formatting and output structure【21†L253-L256】.
- Crisol Translations, *“Placeholders in Translation”* (Feb 2026): defines placeholders and warns *“they should never be translated, altered, or deleted”*【37†L54-L58】 – a golden rule for token integrity【37†L176-L179】.
- Formsuite documentation on Conversational Forms: notes that **presenting one question at a time** in a chat-like interface “boosts completion rates” and lets users focus【54†L22-L30】【54†L76-L80】, guiding our quiz UX design.
- Digivante, *“QA Smoke Testing”*: underlines that automated smoke tests in a CI/CD pipeline quickly detect build-breaking issues, with “automated smoke tests ensure every code commit doesn’t break essential user paths”【57†L183-L190】.

We did not find *project-specific* external docs, so recommendations on module behavior and quiz flow are partly based on these general resources and standard software/UI practices. If there are constraints we were unaware of (e.g. specific UI frameworks or languages), those should be integrated into the plan as needed. 

