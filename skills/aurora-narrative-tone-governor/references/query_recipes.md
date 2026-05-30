# Query Recipes

Run these commands from the Aurora workspace root.

## Narrative Linter Discovery (full repo)

```bash
rg -n --hidden -S "narrative[ _-]?linter|narrative_linter|narrative-linter|ORION_PROJ_NARRLINT|LINT-NARR" .
```

## Narrative Linter File List (deduplicated)

```bash
rg -l --hidden -S "narrative[ _-]?linter|narrative_linter|narrative-linter|ORION_PROJ_NARRLINT|LINT-NARR" . | sort -u
```

## Tone/LLM Writing Discovery (broad)

```bash
rg -n --hidden -S "\\btone\\b|\\bcadence\\b|voice consistency|llm|large language model|prompt engineering|meta[- ]narration|fake[- ]depth|audience clarity|anti[- ]flourish|writing style" .
```

## Canonical-Scope Tone Search (recommended default)

```bash
rg -n --hidden -S "\\btone\\b|\\bcadence\\b|voice consistency|llm|large language model|prompt engineering|meta[- ]narration|fake[- ]depth|audience clarity|anti[- ]flourish|writing style" \
  GUMAS_SIM_2.0/02_DEVELOPMENT/Project_Main/Project_Files_GUMAS2_0 \
  GUMAS_SIM_2.0/07_INDICES/Indices
```

## Canonical Governance Anchors

```bash
rg -n "CadenceToneLinterModule|ORION_PROJ_NARRLINT|Narrative_Output_Protocol_Anti-Flourish|NarrativeLinter" \
  GUMAS_SIM_2.0/07_INDICES/Indices/_INDEX_CANONICAL_FILES.csv
```

## Hit and File Counts

```bash
echo "hits=$(rg -n --hidden -S 'narrative[ _-]?linter|narrative_linter|narrative-linter|ORION_PROJ_NARRLINT|LINT-NARR' . | wc -l | tr -d ' ') files=$(rg -l --hidden -S 'narrative[ _-]?linter|narrative_linter|narrative-linter|ORION_PROJ_NARRLINT|LINT-NARR' . | wc -l | tr -d ' ')"

echo "hits=$(rg -n --hidden -S '\\btone\\b|\\bcadence\\b|voice consistency|llm|large language model|prompt engineering|meta[- ]narration|fake[- ]depth|audience clarity|anti[- ]flourish|writing style' . | wc -l | tr -d ' ') files=$(rg -l --hidden -S '\\btone\\b|\\bcadence\\b|voice consistency|llm|large language model|prompt engineering|meta[- ]narration|fake[- ]depth|audience clarity|anti[- ]flourish|writing style' . | wc -l | tr -d ' ')"
```
