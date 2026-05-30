# Signal Keywords and Ranking Notes

The pipeline ranks file candidates using three factors:
- Recency (dominant signal)
- Filename signal terms
- Extension signal weights

Path name is the deterministic tie-break.

## Filename signal terms

These terms boost file priority when they appear in filenames.

High-priority examples:
- `manifest`
- `checkpoint`
- `continuity`
- `incident`

Operational examples:
- `execution`
- `log`
- `status`
- `report`
- `risk`
- `deploy`
- `patch`
- `release`
- `audit`

Contextual examples:
- `metadata`
- `summary`
- `thread`
- `alignment`
- `index`

## Extension signal weights

Default weight intent:
- `.json`: highest structured signal
- `.csv`: tabular KPI and matrix signal
- `.md`: narrative and status signal
- `.zip`: container artifact (members scanned separately)

## Markdown cue terms

Risk cue examples:
- `risk`
- `blocked`
- `failed`
- `incident`
- `degraded`
- `rollback`
- `hotfix`

Action cue examples:
- `todo`
- `action`
- `next step`
- `owner`
- `follow up`
- `mitigate`
- `remediate`

## Sensitive token detection cues

The analyzer tracks and redacts likely secret patterns such as:
- Private key markers
- API key assignments
- Bearer tokens
- OpenAI-style keys (`sk-...`)
- AWS access key format (`AKIA...`)
- Long token-like alphanumeric strings

Counts are preserved in JSON output under `sensitive_pattern_counts`.
