"""Read-only Drive intake tests; no credentials or network are required."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from drive_recovery_snapshot import SnapshotError, summary


def snapshot():
    return {
        "schema_version": 1,
        "provider": "google_drive",
        "access_class": "private",
        "records": [{
            "source_id": "id-1",
            "title": "Historical reference",
            "mime_type": "text/plain",
            "source_url": "https://drive.google.com/file/d/id-1/view",
            "review_status": "pending_review",
            "promotion_status": "not_promoted",
            "content_sha256": None,
            "repository_matches": [{
                "repository": "AUo959/aurora-cloudbank-symbolic",
                "path": "modules/example.py",
                "relationship": "candidate",
                "authority": "none",
            }],
        }],
    }


class DriveSnapshotTests(unittest.TestCase):
    def test_aggregate_report_hides_private_metadata(self):
        result = summary(snapshot())
        self.assertEqual(result["record_count"], 1)
        self.assertEqual(result["matched_record_count"], 1)
        self.assertNotIn("id-1", str(result))
        self.assertEqual(result["promotion_status"], "not_promoted")

    def test_cannot_promote_external_content(self):
        bad = copy.deepcopy(snapshot())
        bad["records"][0]["promotion_status"] = "canonical"
        with self.assertRaises(SnapshotError):
            summary(bad)

    def test_cannot_mistake_metadata_for_content_digest(self):
        bad = copy.deepcopy(snapshot())
        bad["records"][0]["content_sha256"] = "a" * 64
        with self.assertRaises(SnapshotError):
            summary(bad)

    def test_rejects_duplicate_ids_and_embedded_contents(self):
        bad = copy.deepcopy(snapshot())
        bad["records"].append(copy.deepcopy(bad["records"][0]))
        with self.assertRaises(SnapshotError):
            summary(bad)
        bad = snapshot()
        bad["records"][0]["raw_text"] = "private content"
        with self.assertRaises(SnapshotError):
            summary(bad)


if __name__ == "__main__":
    unittest.main()
