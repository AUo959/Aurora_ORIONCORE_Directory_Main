# Canon Operations Bridge

The read adapter implements the pinned CanonRec v1 query contract against a local Git object database. Supply the full CanonRec data commit and explicit paths within one canon layer. The adapter reads committed JSON and newline-delimited JSON records. It checks request and result shapes against the published schemas at the separate, fixed contract revision. [CanonRec contract](https://github.com/AUo959/CanonRec/tree/778ba3b3aced338f30bc4b35accecf14ecf419a3/contracts/canon-ops/v1) · [Bridge issue #48](https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/issues/48)

```bash
python tools/canon_ops_query.py --canonrec /path/to/CanonRec query.json
```

The local Python environment needs `jsonschema` and its date-time format support. The CanonRec clone must contain the contract and data commits before the command runs. The query itself makes no network requests.

Entity IDs use the canonical record identifier. Aliases match names, recorded alternate identifiers, and aliases case-insensitively. Relationship filters match an explicit relationship pair or a matching native field ending in `_id` or `_ids`. Time filters use inclusive bounds. The adapter returns a source repository, path, layer, commit, and SHA-256 for each result. Requests with the same scope and pinned data return the same ordered page and cursor.

Station Chronicle entries are operational atoms. For a record without a native certainty tag, the adapter uses `UNCONFIRMED` and preserves the original record in the result. Collection labels distinguish sources by evidence status. CanonRec continues to own certainty and promotion decisions.
