from pathlib import Path
from unittest import TestCase


ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
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
