# Aurora plug-in constellation landing

Scope: AUo959/aurora-cloudbank-symbolic PR #1622, authored commit
`b60f3c3db3ab96fd770c3a3604b4ee6cbbbc8908` against
`0fac980967ac7802a399f091fadf24bcd67b3126`.

The owner requested landing the prepared consolidation. Four files clarify
RiverThread/Archy identity, preserve historical linkage, reconcile Aurora's
historical configuration with current implementation and symbolic state, and
map nine plug-in responsibilities. Picard_Delta_3 and canon authority remain
intact. Installed packages and runtime state are unchanged.

Validation: 10 canon provenance/consistency tests passed with the existing
CloudBank Python environment (`pytest --noconftest -q -o addopts=''`). Nine
instruction/manifest snapshots, 104 reference hashes (64 distinct byte hashes),
16 repository evidence hashes, document links and identity separation were
checked. The full application suite was not run locally for this documentation
change. CloudBank CI is tracked on the PR, independently of these local checks.

The provenance inventory is `docs/plugins/provenance.json` in CloudBank.
Byte-identical references count as one evidence family; differing hashes are
not proof of independent origin. CanonRec was inspected read-only; its remote
freshness was not verified.

The root receipt is isolated from the existing health PR #91. No unrelated
health commits are included. Peer-review debt for domain
`plugin-constellation-guidance` is recorded in session state under the adopted
async review-debt policy. This is a pending complementary review, not a passing
peer-review receipt and not a prerequisite waived by CI.
