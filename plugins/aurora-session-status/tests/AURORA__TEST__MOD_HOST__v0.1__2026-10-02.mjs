import assert from "node:assert/strict";
import { register, formatLines } from "../hooks/AURORA__MOD__SESSION_STATUS__v0.1__2026-10-02.mjs";

const handlers = new Map();
register((event, options, handler) => handlers.set(event, handler ?? options));
assert.deepEqual([...handlers.keys()], ["session.start", "turn.complete", "ui.render"]);
let calls = 0;
const data = { schema_version: 1, mode: "read_only", target_repo: "root", branch: "feature",
  active_task: "test", claims: {active: 1, stale: 0}, cloudbank: {pin: "abcdef123", status: "match"},
  waiting_items: [], next_action: "Review", warnings: [] };
const host = { session: {cwd: async () => "/workspace/space name"}, process: {
  run: async argv => {
    calls++;
    assert(Array.isArray(argv));
    return {exitCode: 0, stdout: argv[0] === "git" ? "/workspace/space name\n" : JSON.stringify(data)};
  }}, ui: {invalidate() {}, resolve: () => ({Box: x => x, Text: x => x})}};
const event = {value: "unchanged"};
assert.equal(await handlers.get("session.start")(host, event, async e => e), event);
assert.equal(calls, 2);
const original = {children: "other mod"};
let rendered = handlers.get("ui.render")(host, {}, () => original);
assert.equal(rendered.children[0], original);
assert.equal(handlers.get("ui.render")(host, {hasSurvey: true}, () => original), original);
await handlers.get("turn.complete")(host, {agentId: "subagent"}, async e => e);
assert.equal(calls, 2);
assert(formatLines({...data, next_action: "\u001b[31munsafe\ntext"}, 30).every(x => x.length <= 28 && Array.from(x).every(character => character.codePointAt(0) >= 32)));
host.process.run = async () => {throw Error("missing Python");};
await handlers.get("turn.complete")(host, event, async e => e);
rendered = handlers.get("ui.render")(host, {}, () => original);
assert(rendered.children.some(x => String(x.children).includes("unavailable")));
console.log("Mod host contract: passed (composition, passthrough, narrow width, failure refresh)");
