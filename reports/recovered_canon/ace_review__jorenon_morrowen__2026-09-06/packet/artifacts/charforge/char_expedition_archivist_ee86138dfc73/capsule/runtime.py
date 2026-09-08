#!/usr/bin/env python3
"""
Minimal capsule runtime (stdlib only).

Commands:
  validate  - verify capsule/manifest.json hashes (excluding manifest itself)
  compile   - print a compact "system/user" prompt pack (JSON) from capsule files
  state     - print state.bin length + basic stats
"""
import argparse, hashlib, json, struct
from pathlib import Path

CAP_FILES = [
    "identity.json", "traits.json", "knowledge.jsonl",
    "cns.yaml", "state.bin", "runtime.py", "manifest.json",
]

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))

def load_jsonl(p: Path):
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(json.loads(line))
    return out

def cmd_validate(root: Path):
    man  = load_json(root / "manifest.json")
    recs = {r["path"]: r["sha256"] for r in man.get("records", [])}
    ok   = True
    for name in CAP_FILES:
        if name == "manifest.json":
            continue
        expect = recs.get(name)
        if not expect:
            print(f"FAIL missing manifest entry: {name}")
            ok = False
            continue
        got = sha256_file(root / name)
        if got != expect:
            print(f"FAIL {name} expected {expect} got {got}")
            ok = False
    print("PASS" if ok else "FAIL")

def cmd_compile(root: Path):
    identity  = load_json(root / "identity.json")
    traits    = load_json(root / "traits.json")
    cns       = load_json(root / "cns.yaml")   # JSON stored in .yaml
    knowledge = load_jsonl(root / "knowledge.jsonl")
    pack = {
        "system": {
            "anchor_seed":      identity.get("anchor_seed"),
            "ethics_protocol":  identity.get("ethics_protocol"),
            "declared_layer":   identity.get("declared_layer"),
            "tool_policy":      cns.get("tool_policy"),
            "self_checks":      cns.get("self_checks"),
        },
        "user": {
            "traits":    traits,
            "knowledge": knowledge,
        },
    }
    print(json.dumps(pack, indent=2, sort_keys=True))

def cmd_state(root: Path):
    b    = (root / "state.bin").read_bytes()
    n    = len(b) // 2
    vals = struct.unpack("<" + "e" * n, b)   # float16
    mn   = min(vals) if vals else 0.0
    mx   = max(vals) if vals else 0.0
    print(json.dumps({
        "bytes": len(b), "float16_count": n,
        "min": float(mn), "max": float(mx),
    }, indent=2))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["validate", "compile", "state"])
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    if args.cmd == "validate":
        cmd_validate(root)
    elif args.cmd == "compile":
        cmd_compile(root)
    else:
        cmd_state(root)

if __name__ == "__main__":
    main()
