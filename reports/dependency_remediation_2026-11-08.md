# Dependency security maintenance completion

Scope: the owner's approved runtime/frontend dependency-remediation batch after
queue recovery. November 8 UTC / November 7 in New York.

## Patch and boundary

CloudBank [PR #1686](https://github.com/AUo959/aurora-cloudbank-symbolic/pull/1686)
replaces certifi 2026.7.22 with 2026.10.23, MCP 1.29.1 with 1.30.0, PyJWT 2.13.0
with 2.15.1, and urllib3 2.7.0 with 2.8.0. Requirements sources, standalone
connector/SSE metadata, plain lock, and hashed runtime/CI locks agree. MCP v1
APIs and the v2 compatibility ceiling remain unchanged. Unrelated Python
package versions and markers are preserved.

Frontend security updates retain application framework majors. DOMPurify is
exactly pinned to 3.4.17, Vitest remains on major 4, Vite's baseline requires a
patched release, and a qualified minimatch override replaces affected majors
without overriding unaffected older copies.

An override alone missed the actual runtime boundary: Monaco contains a
vendored sanitizer and the React wrapper defaults to a CDN copy. The editor now
uses local ESM and local workers; its sanitizer import resolves to the patched
package. Production module-graph checks reject the vendored copy. A separate
review found the development optimizer retaining that copy; excluding Monaco
from prebundling, with optimizer/transform and browser checks, closes that path.
The anchor scanner excludes gitignored dist output so a normal post-build
backend test run does not index the generated/minified editor bundle.

## Verification

- Original version-matching audits: four Python packages / 23 unique advisory
  IDs and 39 frontend affected packages, including critical/high findings.
- Fresh runtime and full frontend audits: zero known advisory findings. This
  is point-in-time dependency evidence, not a repository-wide security claim.
- Hash-verified isolated installation from the CI lock succeeds.
- The shared-options JWT regression fails against 2.13.0 and passes against
  2.15.1; expired tokens are rejected, valid tokens accepted, and options remain
  unmodified. The application itself uses fixed HS256 without shared unverified
  options, so no claim is made that this path was already exploitable there.
- The shadow-root template regression fails against DOMPurify 3.4.12 and passes
  against 3.4.17 for template-literal, Mustache, and ERB forms. Ordinary HTML and
  shadow text remain usable. Monaco's observed settings do not enable the
  advisory's template mode; dependency remediation is distinct from a proved
  application exploit.
- Six frontend security checks pass, plus type-check, strict lint and production
  build. Chromium verifies Python/JavaScript typing, light theme, local workers,
  no Monaco CDN requests, and no page errors. Development requests target the
  patched sanitizer. External font CSS is stubbed for deterministic smoke.
- Python focused checks: 99 passed / 79 existing live-backend skips. Fourteen
  additional mocked connector transport/schema checks pass with a local test
  token. A real MCP stdio handshake lists all five schemas without a live API.
- Source-scanner/post-build focused checks pass while preserving authored files.
- Full local suite in the thread-limited numerical-library environment: 3,738
  passed / 113 skipped / 9 xfailed / 2 xpassed. A preceding default-thread run
  hit the quantum-conversion timing threshold; no assertion or threshold was
  relaxed. The exact final-head CI result is recorded below.
- Final CI: final reviewed head `fd12bbd8` passed required CI with 3,738 passed /
  113 skipped / 9 xfailed / 2 xpassed, plus 101 subtests passed. The default
  CI numerical test also passed; no numerical code or threshold was changed.

The independent pre-patch investigator confirmed the vendor/CDN boundary.
The separate candidate reviewer was unavailable due to its usage limit, so the
parent performed the bypass/regression pass. That pass caught the development
optimizer copy and standalone MCP requirement before landing. No skipped check
is represented as passed. Live production/provider access was not tested.

## Overlapping PR review

The following dependency-only proposals are covered by the newer patch;
all nine were closed after successful landing, with heads rechecked against
the analyzed revisions. Proposed Python floors and every changed frontend
lock version are covered by the merged patch. Branches/history are preserved.

| PR | Proposed | Replacement in this batch |
| --- | --- | --- |
| #1678 | certifi 2026.10.18 | 2026.10.23, including trust-store correction |
| #1655 | MCP 1.30.0 | same, plus standalone connector bounds |
| #1621 | PyJWT 2.15.0 | 2.15.1 |
| #1623 | urllib3 2.8.0 | same |
| #1683 | Vite 8.3.6 | same, with patched minimum |
| #1684 | undici 8.12.4 | same |
| #1666 | follow-redirects 1.16.2 | same |
| #1656 | source-map-js 1.2.2 | same |
| #1644 | brace-expansion 5.0.12 | same |

Older Vite #1659 and undici #1657 generations were already closed before
this cleanup; they are not counted as closures by this batch.

Grouped upgrade PRs retain potentially independent work and are not assumed
superseded. Branches and payload history are preserved.

## Landing and queue receipt

CloudBank #1686 merged at `149b12450e87b180a88b4de81a66393f44145df6`
after all applicable checks passed. Closed covered proposals: #1678, #1655,
PR #1621, #1623, #1683, #1684, #1666, #1656, #1644. Grouped proposals remain open.
The root registry, Orion repository policy pin, and independent preflight test
attestation now bind that merged revision. The simulation tree is unchanged;
runtime owner blob remains `5b6d93515fb219cb26d267db6c6df6c052413ae1`.
The targeted dependency-security queue item is completed by this receipt.
Root validation: 747 passed / 41 skipped; session-state schema and explicit
registry checks pass. Queue: 37 open items (32 ready, 5 waiting); 37 overdue
reviews retain their original dates. Broader optional/image audits and the
existing CloudBank security/CVE-audit item are not declared complete by these
two lockfile audits.

The targeted dependency-security maintenance item can complete once the patch
and verification land. Broader code-security work, CI consolidation, and the
MCP v2 migration remain separate tasks; no canon promotion or live simulation
execution is performed. Confidence 0.98 for bounded audit and test observations.
