# Drop-In Thread Context Tagging Agent

import re
import json

# Define symbolic categories
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


def tag_thread_context(content: str):
    scores = {k: 0 for k in PROJECT_CATEGORIES}
    content_lower = content.lower()

    for category, keywords in PROJECT_CATEGORIES.items():
        for kw in keywords:
            if kw in content_lower:
                scores[category] += 1

    sorted_categories = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_category, top_score = sorted_categories[0]

    return {
        "folder": top_category if top_score > 0 else "Unsorted",
        "priority": "high" if top_score > 2 else "medium" if top_score > 0 else "low",
        "reason": f"Matched {top_score} keyword(s) for category '{top_category}'"
    }


# Example usage
if __name__ == "__main__":
    # Simulate pasted thread content (in practice, drop the agent into the thread itself)
    example_text = "We're dealing with anchor routing and THREADCORE drift logic. Also working on GitHub push."
    result = tag_thread_context(example_text)
    print(json.dumps(result, indent=2))
