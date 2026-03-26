from __future__ import annotations

from typing import Dict, List, Optional

from memory_system_prototype import MemoryItem, MemoryStore

class MemorySystem:
    """
    High-level manager for multiple MemoryStores, corresponding to different types or owners of memory.
    """
    def __init__(self):
        # Dictionary of stores: e.g., {"Galactic Union": MemoryStore(...), "Chancellor Zylox": MemoryStore(...), ...}
        self.stores: Dict[str, MemoryStore] = {}
        # Global parameters for performance tuning
        self.max_active_per_store: int = 1000  # example: cap on active memories per store (to trigger compression)
        self.auto_compress: bool = True        # whether to auto-compress when cap is exceeded

    def create_store(self, name: str) -> MemoryStore:
        """
        Create a new memory store for a given entity or category.
        """
        store = MemoryStore(name)
        self.stores[name] = store
        return store

    def get_store(self, name: str) -> Optional[MemoryStore]:
        """
        Retrieve a MemoryStore by name.
        """
        return self.stores.get(name)

    def add_memory(self, memory_type: str, owner: str, content: str, importance: float = 1.0, tags: List[str] = None):
        """
        Convenience method to create and add a memory to the appropriate store.
        :param memory_type: Category of memory (faction, agent, etc).
        :param owner: The entity for whom this memory is being added (could be a faction name or agent name).
        :param content: The content of the memory.
        :param importance: Importance score of the memory.
        :param tags: Optional list of tags for relevance.
        """
        # Ensure a store exists for this owner (create if not)
        if owner not in self.stores:
            self.create_store(owner)
        memory = MemoryItem(content, memory_type, owner=owner, importance=importance, tags=tags)
        self.stores[owner].add_memory(memory)
        # Optionally trigger compression if too many active memories
        if self.auto_compress and len(self.stores[owner].active_memories) > self.max_active_per_store:
            self.compress_store(owner)

    def compress_store(self, store_name: str):
        """
        Compress older or less important memories in the given store to keep memory size in check.
        This could, for example, summarize the oldest half of the memories.
        """
        store = self.stores.get(store_name)
        if not store:
            return
        memories = store.active_memories
        if not memories:
            return
        # Simple strategy: sort by a combination of age and low importance to decide what to compress
        memories.sort(key=lambda m: (m.importance, m.timestamp))
        # Take roughly the oldest/least important half for compression
        cutoff = len(memories) // 2
        to_compress = memories[:cutoff]
        if not to_compress:
            return
        # Generate a summary content (placeholder logic: join summaries or count events)
        summary = f"Summary of {len(to_compress)} events: "
        # e.g., list key phrases or just a generic note for now
        summary += "; ".join(mem.content.split('.')[0] for mem in to_compress[:3])
        if len(to_compress) > 3:
            summary += "; ... and other events."
        # Use the store's compress_and_archive to handle moving and archiving
        store.compress_and_archive(summary_content=summary, affected_memories=to_compress)

    def decay_all(self, elapsed_time: float):
        """
        Decay memories in all stores by the given elapsed time.
        This should be called periodically (e.g., each simulation tick or hour).
        """
        for store in self.stores.values():
            store.decay_memories(elapsed_time)

    def retrieve_context(self, owner: str, query: str, include_related: bool = True, top_k: int = 5) -> List[MemoryItem]:
        """
        Retrieve relevant memories across one or multiple stores for a given context.
        :param owner: The primary owner/entity whose memory we query (e.g., an agent name).
        :param query: Context or query string describing what is currently relevant.
        :param include_related: If True, also search related stores (like faction or global memory related to the owner).
        :param top_k: Number of memories to retrieve *per store* (the final context may include more if multiple stores are combined).
        :return: List of MemoryItems relevant to the query from the relevant stores.
        """
        results: List[MemoryItem] = []
        primary_store = self.stores.get(owner)
        if primary_store:
            results.extend(primary_store.retrieve_memories(query=query, top_k=top_k))
        if include_related:
            # Example of related: if owner is an agent, maybe also look at their faction's store or global history.
            # This logic can be customized based on naming conventions or metadata.
            # For simplicity, assume if owner has a faction tag in store name or memory_type, or known mapping:
            related_stores: List[MemoryStore] = []
            # If the owner store is of type agent and we have a faction store named after a faction in owner tags:
            # (This requires some mechanism to know faction membership; could be stored in MemoryItem tags or a mapping.)
            # Here we just loop through all stores and pick faction/global types as an example.
            for name, store in self.stores.items():
                if name == owner:
                    continue
                # Suppose faction store names contain "Faction" or match an agent's faction tag
                # (In practice, you'd have a mapping of agent->faction)
                if store.name.lower() in query.lower():  # naive: if faction name appears in query
                    related_stores.append(store)
                # or if owner's memory items have a tag for this store name
            for store in related_stores:
                results.extend(store.retrieve_memories(query=query, top_k=top_k))
        # Optionally sort all results by importance or recency across stores, but since each store is already sorted, we can return as is.
        return results
