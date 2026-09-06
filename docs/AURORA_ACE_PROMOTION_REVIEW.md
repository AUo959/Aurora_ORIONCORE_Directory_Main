# Sandbox character promotion review

The root-owned `tools/aurora_ace_promotion.py` connects a completed sandbox
creation to Aurora's existing reconciliation and native materialization tools.
It produces an offline review packet in a new directory. Canonical repositories
and the persistent world are read-only inputs; only an independent rehearsal
clone receives a native commit. The sandbox's three MCP tools remain unchanged.

## Capability reuse

| Responsibility | Existing owner reused |
| --- | --- |
| World identity, confinement, serialized access | `ace.sandbox.World` |
| Original determination validation | `ace.materialize._validate_receipt` |
| Packet completeness and original artifact hashes | Native character packet layout and ACE determination integrity fields |
| Canonical ID, name, alias lookup | `ace.character_retrieval.discover_character_candidates` |
| Current target name registry | CanonRec `export_name_registry.py` |
| Entity schema and context scan | CanonRec `validate_entity.py` |
| Naming admission | CanonRec `validate_naming_receipts.py` |
| Reconciliation recommendation | CanonRec `reconciliation_advisor.py` |
| Machine-readable validation provenance | CanonRec `emit_evidence_receipt.py` |
| Complete native character transaction | `ace.character_materialize.materialize_character_packet` |
| Determination history | Existing ACE ledger, written inside the review directory |
| Later authenticated draft-PR publication | Existing `ace.delegated_publication.publish_delegated_packet`; not invoked by this command |

NameService and CharForge already supplied the source character. Review preserves
their original output; it does not generate a replacement character. Generic
entity, facility, and Orion progression capabilities remain with their existing
owners and are not needed for this character-only handoff.

## Operator commands

Run from the implementation checkout with the dedicated Python 3.12 environment:

```sh
/Users/travisstreets/dev/aurora-ace-runtime/bin/python tools/aurora_ace_promotion.py prepare \
  --world /Users/travisstreets/dev/aurora-ace-sandbox \
  --request-id demo-create-one \
  --target-root /Users/travisstreets/dev/Aurora_ORIONCORE_Directory_Main \
  --output /Users/travisstreets/dev/aurora-ace-reviews/jorenon-morrowen-20260906

/Users/travisstreets/dev/aurora-ace-runtime/bin/python tools/aurora_ace_promotion.py verify \
  --output /Users/travisstreets/dev/aurora-ace-reviews/jorenon-morrowen-20260906
```

The example output directory was created by the verified demonstration. A later
review must use a new destination; existing reviews are never overwritten.

Read `REVIEW.md` first, then `promotion_review.json`, the validation and naming
reports, reconciliation advice, and evidence receipt. A `review_ready` result
includes `proposal.patch`, the exact diff produced by the native materializer
inside the rehearsal clone. The complete original packet and source creation
determination remain available alongside the rehearsal determination.

The advisor's certainty recommendation is advisory and does not rewrite the
original packet or determine canon authority. `review_ready` means the local
rehearsal passed, not `CANON_PROMOTE` approval for the source world.

## Freshness and authority

The review binds the local target CanonRec HEAD, original packet baseline, source
creation commit, and evidence hashes. It does not claim remote-main freshness.
`verify` checks artifact hashes and current local target HEAD/cleanliness.

Existing identities, name collisions, modified packet inputs, dirty target
checkouts, unsafe paths, or a changed baseline refuse a ready proposal. A source
packet created after sandbox-only commits can have a different baseline from
canonical CanonRec; this is reported as blocked. The bridge does not rewrite
historical baselines. A future ACE revalidation determination must account for
that difference before the native materializer can accept it.

Publication remains the responsibility of the existing policy-gated delegated
publisher, which requires authenticated authority, a registered baseline,
remote-main freshness, and a draft PR. This review command does not call it,
push nested branches, merge canon, or advance Orion. The publication handoff is
therefore prepared and reviewable, not activated by a sandbox creation request.

## Verification

```sh
ACE_PROMOTION_E2E=1 python -m pytest tests/test_aurora_ace_promotion.py -q
```

The tests provision a fresh world from committed root/registered nested revisions,
create a character through ACE, and rehearse against an independent target copy.
Outside a provisioned checkout, set `ACE_SANDBOX_REPOSITORIES_ROOT` to the local
workspace containing the registered nested repositories. CI runs these tests
after the existing composition and persistent-world tests.
