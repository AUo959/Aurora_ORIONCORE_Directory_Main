// Aurora session status. Host APIs follow Anthropic's token-weather sample.
// Hooks pass events unchanged; only the AbovePrompt UI is composed.
let report = null;
let pending = false;

export function register(on) {
  on("session.start", async ($, e, next) => {
    const result = await next(e);
    report = null;
    await refresh($);
    return result;
  });
  on("turn.complete", async ($, e, next) => {
    const result = await next(e);
    if (!e.agentId) await refresh($);
    return result;
  });
  on("ui.render", { component: "AbovePrompt" }, ($, e, next) => {
    const original = next(e);
    if (e.hasSurvey || report === null) return original;
    const { Box, Text } = $.ui.resolve(e);
    const lines = formatLines(report, e.bodyColumns ?? 80);
    return Box({ flexDirection: "column", children: [original,
      ...lines.map(line => Text({ children: line, color: report.warnings?.length ? "yellow" : "cyan" }))] });
  });
}

async function refresh($) {
  if (pending) return;
  pending = true;
  try {
    const cwd = await $.session.cwd();
    const found = await $.process.run(["git", "rev-parse", "--show-toplevel"], { cwd, timeoutMs: 3000 });
    if (found.exitCode !== 0) throw new Error("workspace unavailable");
    const root = found.stdout.trim();
    const run = await $.process.run(["python3", "-B",
      "tools/AURORA__TOOL__SESSION_STATUS__v0.1__2026-10-02.py", "--root", root],
      { cwd: root, timeoutMs: 7000 });
    if (run.exitCode !== 0) throw new Error("status reader unavailable");
    const data = JSON.parse(run.stdout);
    if (data.schema_version !== 1 || data.mode !== "read_only") throw new Error("unsupported status");
    report = data;
  } catch {
    // Never keep a previous healthy-looking snapshot after a failed refresh.
    report = { warnings: ["Aurora status unavailable; check workspace and Python"], target_repo: "unknown" };
  } finally {
    pending = false;
    $.ui.invalidate("ui.render");
  }
}

function clean(value) {
  return String(value ?? "unknown").replace(/[\x00-\x1f\x7f-\x9f]/g, " ");
}

export function formatLines(data, columns = 80) {
  const width = Math.max(10, columns - 2);
  const pin = data.cloudbank?.pin ? clean(data.cloudbank.pin).slice(0, 8) : "unknown";
  const lines = [
    `Aurora | ${clean(data.target_repo)} (${clean(data.target_source)}) | workspace branch: ${clean(data.branch)}`,
    `Task: ${clean(data.active_task)} | local claims: ${data.claims?.active ?? "?"} active, ${data.claims?.stale ?? "?"} stale`,
    `CloudBank: ${pin} ${clean(data.cloudbank?.status)} | queue waits: ${data.waiting_items?.length ?? "?"}`,
    `Next: ${clean(data.next_action)}`,
    "Advisory snapshot; local claims only; no execution approval",
    ...(data.warnings ?? []).map(w => `Warning: ${clean(w)}`),
  ];
  return lines.map(line => line.length > width ? line.slice(0, width - 1) + "…" : line);
}
