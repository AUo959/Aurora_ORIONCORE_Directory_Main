# memory_system.py
from math import exp, log
from typing import List, Optional, Callable, Dict, Any
import time

class MemoryItem:
    """
    Represents a single memory entry in the simulation memory system.
    """
    def __init__(self, content: str, memory_type: str, owner: str = "", 
                 importance: float = 1.0, timestamp: Optional[float] = None, 
                 tags: Optional[List[str]] = None):
        """
        Initialize a MemoryItem.
        :param content: The content or description of the memory (can be text or serialized data).
        :param memory_type: Category of memory (e.g. "faction", "agent", "history", "narrative").
        :param owner: Identifier for whose memory this is (e.g. agent name or faction name).
        :param importance: Importance score (e.g. 1-10 scale) indicating significance of this memory.
        :param timestamp: In-world time when this memory event occurred. If None, uses current real time.
        :param tags: Optional tags or keywords for this memory (for simple relevance matching).
        """
        self.content: str = content
        self.type: str = memory_type
        self.owner: str = owner
        self.importance: float = importance
        self.timestamp: float = timestamp if timestamp is not None else time.time()
        self.last_access: float = self.timestamp  # last time this memory was accessed
        # Decay parameters
        self.strength: float = 1.0    # current memory strength (1.0 = full strength initially)
        self.half_life: float = None  # half-life for decay (computed from importance if not set)
        # By default, set half-life based on importance (higher importance => longer half-life)
        # e.g., base half-life of 1 day for importance=5, scale exponentially.
        # This can be adjusted as needed.
        base_half_life = 24.0 * 3600.0  # 1 day in seconds as baseline
        # importance 5 -> 1 day, importance 10 -> perhaps 1 week, importance 1 -> 1 hour (for example)
        if importance >= 5:
            # exponential growth: each point above 5 doubles half-life roughly
            self.half_life = base_half_life * (2 ** (importance - 5))
        else:
            # importance below 5 shortens half-life: each point below 5 halves it
            self.half_life = base_half_life * (0.5 ** (5 - importance))
        if self.half_life < 1e-6:  # ensure not zero
            self.half_life = 1e-6
        # Tags for simple relevance checking (e.g., ["diplomacy","Velar Imperium"])
        self.tags: List[str] = tags or []
        # Conflict flag or reference to other memories (for conflict resolution if needed)
        self.status: str = "active"   # could be "active", "archived", "invalidated", etc.
        self.ref_id: Optional[str] = None  # optional ID to link to other related memory (e.g., same event ID)

    def decay_strength(self, elapsed_time: float):
        """
        Decay the memory's strength based on elapsed time (in seconds).
        Uses exponential decay: strength *= exp(-lambda * t), where lambda is derived from half_life.
        """
        if self.strength <= 0 or self.half_life is None:
            return
        # lambda such that half-life yields half strength: lambda = ln(2) / half_life
        lam = log(2) / self.half_life
        # apply decay
        self.strength *= exp(-lam * elapsed_time)
        # If strength falls below a tiny threshold, set to 0 (effectively forgotten)
        if self.strength < 1e-6:
            self.strength = 0.0

    def reinforce(self, amount: float = 0.5):
        """
        Reinforce (boost) the memory's strength, e.g., after being recalled or used.
        :param amount: The amount to boost (relative to remaining gap to full strength).
        """
        # Boost strength by a fraction of the difference to 1.0, capped at 1.0.
        # For example, amount=0.5 will bring strength halfway toward full (like a learning rate).
        if self.strength < 1.0:
            self.strength += (1.0 - self.strength) * amount
        # Also reset last access time to now (recently used)
        self.last_access = time.time()


class MemoryStore:
    """
    Stores and manages a collection of MemoryItem objects for a particular category or owner.
    For example, a MemoryStore might hold all memories of a single agent or faction.
    """
    def __init__(self, name: str):
        """
        :param name: Identifier for this store (could be an agent name, faction name, or category).
        """
        self.name: str = name
        # Active and archived memories
        self.active_memories: List[MemoryItem] = []
        self.archived_memories: List[MemoryItem] = []
        # Optional function for computing similarity between a query and a memory (for relevance)
        # This can be set to an embedding-based function for advanced use.
        self.similarity_fn: Optional[Callable[[str, MemoryItem], float]] = None

    def add_memory(self, memory: MemoryItem):
        """
        Add a new MemoryItem to the active memory list.
        """
        self.active_memories.append(memory)

    def retrieve_memories(self, query: Optional[str] = None, top_k: int = 5, current_time: Optional[float] = None
                          ) -> List[MemoryItem]:
        """
        Retrieve relevant memories from this store, sorted by a combined relevance score.
        :param query: An optional context or query string to match for relevance. If None, use only recency & importance.
        :param top_k: Maximum number of memories to return.
        :param current_time: Current time for recency calculations (defaults to now if not provided).
        :return: List of MemoryItem objects that are most relevant.
        """
        if current_time is None:
            current_time = time.time()
        scored_memories: List[tuple[float, MemoryItem]] = []
        for mem in self.active_memories:
            if mem.strength <= 0 or mem.status != "active":
                continue  # skip forgotten or inactive memories
            # Calculate components for score
            # 1. Recency (time since last access, smaller gap = higher score)
            time_since_access = current_time - mem.last_access
            # Recency score: exponential decay or simpler inverse
            recency_score = exp(-0.001 * time_since_access)  # with 0.001 per second (~0.06 per minute)
            # 2. Importance score (normalized to 0-1 range assuming importance max ~10)
            importance_score = mem.importance / 10.0
            # 3. Relevance score (if query given)
            if query:
                if self.similarity_fn:
                    # Use custom similarity function if provided (e.g., embedding similarity)
                    rel_score = self.similarity_fn(query, mem)
                else:
                    # Simple relevance: check if any tag or content keyword matches query
                    text = mem.content.lower()
                    q = query.lower()
                    # for simplicity, relevance as fraction of query words present in memory text
                    matches = sum(1 for word in q.split() if word in text or word in mem.tags)
                    rel_score = matches / (len(q.split()) + 1e-6)
                # (Alternatively, could use cosine similarity on embeddings if set up)
            else:
                rel_score = 0.0
            # Weighted combination (weights can be adjusted globally if needed)
            # Here we weight recency, importance, and relevance equally for simplicity
            combined_score = recency_score + importance_score + rel_score
            scored_memories.append((combined_score, mem))
        # Sort by score descending and take top_k
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        top_memories = [mem for (_score, mem) in scored_memories[:top_k]]
        # Mark these as accessed now (update last_access and maybe decay others)
        now = time.time()
        for mem in top_memories:
            mem.last_access = now
            # Optionally, reinforce slightly on retrieval to prolong its life
            mem.reinforce(amount=0.1)
        return top_memories

    def decay_memories(self, elapsed_time: float):
        """
        Apply decay to all active memories. Also possibly move very weak memories to archive or remove them.
        :param elapsed_time: Time in seconds to decay by.
        """
        to_archive: List[MemoryItem] = []
        remaining_active: List[MemoryItem] = []
        for mem in self.active_memories:
            mem.decay_strength(elapsed_time)
            if mem.strength <= 0:
                # Memory effectively forgotten: archive it (or drop completely)
                mem.status = "archived"
                to_archive.append(mem)
            else:
                remaining_active.append(mem)
        # Update active list (remove decayed ones)
        self.active_memories = remaining_active
        # Move forgotten memories to archive list (we keep them as record, but not active)
        if to_archive:
            self.archived_memories.extend(to_archive)

    def compress_and_archive(self, summary_content: str, affected_memories: List[MemoryItem]):
        """
        Create a compressed summary memory from a list of old memories, and archive those old ones.
        :param summary_content: The textual summary representing the combined knowledge of affected memories.
        :param affected_memories: List of MemoryItems to be summarized.
        """
        if not affected_memories:
            return
        # Determine an importance for the summary (maybe max of affected or a function of them)
        summary_importance = max(m.importance for m in affected_memories)
        summary_item = MemoryItem(content=summary_content, memory_type=affected_memories[0].type,
                                  owner=self.name, importance=summary_importance,
                                  timestamp=max(m.timestamp for m in affected_memories))
        summary_item.status = "active"
        # Add summary to active memories
        self.active_memories.append(summary_item)
        # Archive the affected memories
        for mem in affected_memories:
            mem.status = "archived"
            mem.strength = 0.0
            self.archived_memories.append(mem)
            # Remove them from active list if still present
            if mem in self.active_memories:
                self.active_memories.remove(mem)
        # Note: In a real system, `summary_content` could be generated by a language model or a custom summarizer.

    def set_similarity_function(self, sim_fn: Callable[[str, MemoryItem], float]):
        """
        Configure a custom similarity function for relevance scoring.
        The function should take a query string and a MemoryItem, and return a float similarity score.
        """
        self.similarity_fn = sim_fn
