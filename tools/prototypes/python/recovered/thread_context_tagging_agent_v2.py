# 🔍 Drop-In Thread Context Tagging Agent v2.0
# Evaluates real symbolic thread content and returns a live classification context

import re
import json

# 📘 LIVE CONTEXT DIRECTIVE
LIVE_CONTEXT_DIRECTIVE = """
⚠️ LIVE CONTEXT MODE ACTIVE

You are being asked to evaluate the actual content of the thread.
Return a true classification – not an example or template output.

✅ Return based on real content
✅ DO NOT simulate or placeholder output
✅ This is used for routing, sealing, or archive classification
"""

# 🧭 Symbolic Project Categories
PROJECT_CATEGORIES = {
    "SymbolicOps": ["THREADCORE", "symbolic", "anchor", "drift", "vector", "reflect", "seal"],
    "GitOps": ["github", "commit", "repo", "branch", "merge", "PR"],
    "SiteBuilder": ["html", "css", "website", "page", "image", "LaFinca"],
    "SecurityCore": ["encryption", "key", "decrypt", "auth", "secure", "session"],
    "DataFlow": ["vector index", "dataset", "cloudsync", "memory", "export"],
    "RitualUX": ["ritual", "arch", "scroll", "map", "invocation", "resilience"],
    "AutomationEngine": ["bot", "agent", "automation", "API", "workflow", "routine"],
    "Diagnostics": ["error", "bug", "trace", "status", "log", "issue"]
}

# 🧠 Core Function
def tag_thread_context(content: str, include_directive: bool = True):
    scores = {k: 0 for k in PROJECT_CATEGORIES}
    content_lower = content.lower()

    for category, keywords in PROJECT_CATEGORIES.items():
        for kw in keywords:
            if kw in content_lower:
                scores[category] += 1

    sorted_categories = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_category, top_score = sorted_categories[0]

    result = {
        "folder": top_category if top_score > 0 else "Unsorted",
        "priority": "high" if top_score > 2 else "medium" if top_score > 0 else "low",
        "reason": f"Matched {top_score} keyword(s) for category '{top_category}'"
    }

    if include_directive:
        result["directive"] = LIVE_CONTEXT_DIRECTIVE.strip()

    return result

# 🧪 Example Usage (Can be removed for production)
if __name__ == "__main__":
    thread_content = """
    THREADCORE symbolic anchor routing with export seal ritual, plus automation workflow from GitOps.
    """
    tagged = tag_thread_context(thread_content)
    print(json.dumps(tagged, indent=2))
