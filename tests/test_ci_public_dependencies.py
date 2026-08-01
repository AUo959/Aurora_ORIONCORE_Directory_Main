import json
from pathlib import Path
from unittest import TestCase


ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
WORKFLOW_DIR = ROOT / ".github" / "workflows"
CLASSIFICATION_OVERRIDES = ROOT / "catalog" / "classification_overrides.yaml"
CHECK = TestCase()


def test_canonrec_ci_checkout_uses_public_repository_access():
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    CHECK.assertIn("repository: AUo959/CanonRec", workflow)
    CHECK.assertIn("Provision CanonRec L1 ledger (public)", workflow)
    CHECK.assertNotIn("WORKSPACE_REPO_TOKEN", workflow)
    CHECK.assertNotIn("CanonRec L1 ledger (private)", workflow)


def test_public_dependency_workflow_uses_immutable_wheel_only_inputs():
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    action_refs = [
        line.split("@", 1)[1].split()[0]
        for line in workflow.splitlines()
        if "uses: actions/" in line
    ]

    CHECK.assertTrue(action_refs)
    CHECK.assertTrue(all(len(ref) == 40 for ref in action_refs))
    CHECK.assertTrue(all(set(ref) <= set("0123456789abcdef") for ref in action_refs))
    CHECK.assertIn("--only-binary=:all:", workflow)
    CHECK.assertIn("--require-hashes", workflow)
    CHECK.assertIn("requirements-hashed.txt", workflow)
    CHECK.assertNotIn("pip install --upgrade pip", workflow)


def test_all_root_workflows_use_immutable_action_refs():
    action_refs = []
    for workflow_path in sorted(WORKFLOW_DIR.glob("*.y*ml")):
        for line in workflow_path.read_text(encoding="utf-8").splitlines():
            if "uses:" not in line or line.lstrip().startswith("#"):
                continue
            ref = line.split("uses:", 1)[1].strip().split("#", 1)[0].strip()
            if ref.startswith("./"):
                continue
            CHECK.assertIn("@", ref, msg=f"missing action ref in {workflow_path}")
            action_refs.append((workflow_path, ref.rsplit("@", 1)[1]))

    CHECK.assertTrue(action_refs)
    for workflow_path, ref in action_refs:
        CHECK.assertEqual(40, len(ref), msg=f"mutable action ref in {workflow_path}: {ref}")
        CHECK.assertTrue(
            set(ref) <= set("0123456789abcdef"),
            msg=f"non-commit action ref in {workflow_path}: {ref}",
        )


def test_public_metadata_is_managed_root_documentation():
    records = {
        record["current_path"]: record
        for record in json.loads(CLASSIFICATION_OVERRIDES.read_text(encoding="utf-8"))["overrides"]
    }

    CHECK.assertEqual("workspace_doc", records["CONTRIBUTING.md"]["kind"])
    CHECK.assertEqual("policy_file", records["SECURITY.md"]["kind"])
    for path in ("CONTRIBUTING.md", "SECURITY.md"):
        CHECK.assertEqual("docs", records[path]["logical_zone"])
        CHECK.assertEqual("root", records[path]["git_boundary"])
        CHECK.assertEqual("managed", records[path]["status"])
