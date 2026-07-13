"""Doc staleness / correctness auditor.

Scans markdown docs for checkable claims and verifies each against directly
observed ground truth (git tree, real source content, config/version files) --
never doc-to-doc, never bare filename existence. See README.md for the full
evidence policy.
"""

from .models import Claim, ClaimType, Evidence, Finding, Status

__all__ = ["Claim", "ClaimType", "Evidence", "Finding", "Status"]
__version__ = "0.1.0"
