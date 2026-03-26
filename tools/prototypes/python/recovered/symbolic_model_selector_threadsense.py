# Symbolic_ModelSelector_ThreadSense
"""
Aurora TRACECORE-integrated model selector
Combines HeuristicDecisionEngine (HDE) logic with context-aware, passive/active model switching for symbolic threads.
"""

from typing import Dict, Any, Optional, Callable
import asyncio

class HeuristicDecisionEngine:
    """
    Generalized, extensible rule-based engine for AI model evaluation and scoring.
    """
    def __init__(self):
        self.models = {
            "GPT-4": {"creativity": 9, "logic": 9, "narrative": 8, "context_hold": 9, "multimodal": 7, "description": "Balanced, powerful, strong at logic, memory, and tone."},
            "GPT-4o": {"creativity": 9, "logic": 8, "narrative": 8, "context_hold": 8, "multimodal": 10, "description": "Fast, multimodal, best for audio/image integration."},
            "GPT-4.1": {"creativity": 9, "logic": 10, "narrative": 9, "context_hold": 10, "multimodal": 8, "description": "Newest, excels at coding, large context, strong for deep tracework."},
            "Claude": {"creativity": 8, "logic": 7, "narrative": 10, "context_hold": 10, "multimodal": 4, "description": "Excellent narrative structure, gentle, smart, human-like."},
            "Gemini": {"creativity": 7, "logic": 8, "narrative": 7, "context_hold": 6, "multimodal": 7, "description": "Good generalist, factual, average long-context."},
        }
        self.memory = []  # Log of past decisions

    def score(self, task_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scores each model based on weighted sum for task profile keys.
        Returns ranked list. Adds error handling for missing keys.
        """
        weights = task_profile.get("weights", {k: 1 for k in next(iter(self.models.values()))})
        scores = {}
        for name, traits in self.models.items():
            try:
                s = sum(traits.get(k, 0) * weights.get(k, 1) for k in weights)
            except Exception as e:
                s = 0  # Fallback to zero score on error
            scores[name] = s
        ranked = sorted(scores.items(), key=lambda x: -x[1])
        self.memory.append((task_profile, ranked))
        return {"ranked": ranked, "scores": scores}

    def best(self, task_profile: Dict[str, Any]) -> Optional[str]:
        result = self.score(task_profile)["ranked"]
        if not result:
            return None
        return result[0][0]


class SymbolicModelSelectorThreadSense:
    """
    Context-aware model selector for TRACECORE and Constellation threads.
    - Supports operator and passive auto modes.
    - Uses HDE as scoring backend.
    """
    def __init__(self, hde=None, validation_hook: Optional[Callable[[str, str], bool]] = None, logger: Optional[Callable[[str], None]] = None):
        self.hde = hde or HeuristicDecisionEngine()
        self.current_model = "GPT-4o"
        self.task_profile = {}
        self.validation_hook = validation_hook
        self.logger = logger

    def analyze_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # Map context to model weights; support user-defined weights
        base = {"logic": 1, "creativity": 1, "narrative": 1, "context_hold": 1, "multimodal": 1}
        base.update(context.get("custom_weights", {}))
        if context.get("mode") == "symbolic_trace":
            base["logic"] += 2
            base["context_hold"] += 2
        if context.get("deep_narrative"):
            base["narrative"] += 2
        if context.get("multimodal_required"):
            base["multimodal"] += 2
        return {"weights": base}

    def recommend(self, context: Dict[str, Any]) -> Optional[str]:
        profile = self.analyze_context(context)
        self.task_profile = profile
        return self.hde.best(profile)

    def auto_switch_if_safe(self, context: Dict[str, Any]) -> Optional[str]:
        recommended = self.recommend(context)
        if recommended and recommended != self.current_model:
            is_valid = True
            if self.validation_hook:
                is_valid = self.validation_hook(self.current_model, recommended)
            if is_valid:
                previous = self.current_model
                self.current_model = recommended
                if self.logger:
                    self.logger(f"Switched model from {previous} to {recommended}")
                return recommended
            else:
                if self.logger:
                    self.logger(f"Switch from {self.current_model} to {recommended} rejected by validator.")
        return None

    def passive_monitor(self, context: Dict[str, Any]) -> None:
        self.auto_switch_if_safe(context)

    def active_recommendation(self, context: Dict[str, Any]) -> Optional[str]:
        return self.recommend(context)

    async def async_passive_monitor(self, context: Dict[str, Any], interval: float = 10.0):
        while True:
            self.passive_monitor(context)
            await asyncio.sleep(interval)

# Example usage in operator or automation:
# selector = SymbolicModelSelectorThreadSense(logger=print)
# context = {"mode": "symbolic_trace", "deep_narrative": True}
# selector.passive_monitor(context)
# print(selector.current_model)
