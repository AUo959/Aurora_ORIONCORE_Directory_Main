# Aurora Intelligent UI — Private MCP Tunnel Pilot v1

**Owner:** ORIONCORE root control plane
**State:** draft, non-production, requires an explicit ChatGPT connection
**Depends on:** PR #97 (snapshot), PR #98 (authenticated local HTTP retrieval)
**Scope:** one read-only stdio MCP tool for saved Mission Control snapshots

## Rationale

Secure MCP Tunnel is preferable to publicly deploying the ORIONCORE root
workspace merely to give ChatGPT a read-only inspection tool. The tunnel-client
makes outbound HTTPS calls to OpenAI from a trusted host; it does not expose
inbound ports or the local HTTP listener. No Vercel project is needed for this
private trial. Public plugin submission is not supported through this tunnel.

## Tool contract

Server: `tools/aurora_intelligent_ui_mcp.py`
Tool: `get_mission_control_snapshot` (no user-supplied arguments)
Input: `reports/analysis/aurora_mission_control_latest.json` under the trusted
ORIONCORE checkout (optionally `AURORA_UI_ROOT` in the operator environment).
Output: existing `aurora.mission_control.snapshot` v1 with source timestamps,
staleness, health, allowlisted inbox and build lanes.

Tool annotations: read-only; bounded workspace; no open-web searching.
Only stdio is enabled; no additional MCP capabilities, ACE tools, commands,
subprocess operations, simulation execution, publication or canon writes.
An explicitly restricted/recovery-review item withholds its evidence and
replaces the next action with a generic governed-review instruction.

## Testing before connection

From an up-to-date trusted ORIONCORE checkout:

    python3 -m pip install -r requirements-ace-mcp.txt
    python3 -m pytest -q tests/test_aurora_intelligent_ui_bridge.py tests/test_aurora_intelligent_ui_service.py tests/test_aurora_intelligent_ui_mcp.py

CI additionally runs the transport tests under Python 3.12. The stdio
test actually starts the MCP server in a subprocess, performs MCP initialize,
inspects tool discovery/annotations, calls the tool with a saved fixture,
checks redaction and validates missing-source failure.

## Secure MCP Tunnel operator setup (requires user action)

1. In OpenAI Platform tunnel settings, confirm that the intended Platform
   organization is associated with the intended ChatGPT workspace; confirm
   Tunnels Read + Manage to create a tunnel and Read + Use for the runtime.
2. Create an MCP tunnel and a *restricted runtime API key* with Tunnels Read + Use.
   Enter credentials only through your local secret storage. Do not paste
   them into GitHub, the PR, a chat, or screenshots.
3. Install the latest supported tunnel-client and inspect its local help.
   The appropriate OS binary and tunnel_id come from Platform settings.
4. On the trusted Aurora host, set `AURORA_UI_ROOT` to the ORIONCORE checkout
   containing the saved report (optional if running from that checkout).
   Configure the client using a trusted absolute Python/script path.

    tunnel-client help quickstart
    tunnel-client init --sample sample_mcp_stdio_local --profile aurora-ui --tunnel-id <TUNNEL_ID> --mcp-command '/path/to/python /path/to/ORIONCORE/tools/aurora_intelligent_ui_mcp.py'
    tunnel-client doctor --profile aurora-ui --explain
    tunnel-client run --profile aurora-ui

5. With that client healthy and polling, in ChatGPT web open Plugins,
   use Add custom MCP server, choose **Tunnel**, select the same tunnel
   and configure the allowed authentication. Review the risk warning;
   create/install the plugin explicitly.
6. Test by selecting the plugin and asking:
   'Read the Aurora Mission Control snapshot. Give me the report generated_at,
    freshness, counts and top nonrestricted issues. Do not assume live status.'
   Inspect the discovered tool list: exactly one read-only tool.

Official: https://developers.openai.com/api/docs/guides/secure-mcp-tunnels
Official: https://developers.openai.com/plugins/deploy/connect-chatgpt

## Acceptance checklist

- MCP discovery exposes only `get_mission_control_snapshot`.
- Snapshot shape validates against v1 schema; SHA-256 matches saved bytes.
- UI explicitly labels old reports stale and displays source timestamp.
- Restricted recovery detail, absolute paths, commands, and source-private
  fields are absent from tool results.
- Deleting/invalidating source results in a safe error, not a fabricated
  latest report or an implicit report refresh.
- Repeating reads never changes the source bytes or any canon materials.
- Wrong/out-of-scope tool calls cannot access ACE, GUMAS or CanonRec.
- ChatGPT test is only complete after a real user-authorized plugin install
  and successful tool call; GitHub CI cannot certify a remote connection.

## Limits

The saved source currently checked in the repo was dated August 15, 2026;
do not call it current merely because the tool invocation happened today.
Tunnel availability depends on account/workspace permissions and an
operator-running host; the assistant cannot create the account connection
on behalf of a user. Do not merge or publish a private pilot as production
without the normal ORIONCORE gates and operator review.
