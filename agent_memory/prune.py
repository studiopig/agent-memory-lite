"""Auto-pruning logic — keep high-signal memories, discard noise."""

from .storage import Storage


class Pruner:
    """Prune low-importance memories to keep context lean."""

    def __init__(self, storage: Storage):
        self.storage = storage

    def prune(self, keep_ratio: float = 0.8):
        """Keep top X% memories by importance score.

        Also removes near-duplicate memories (content similarity > 90%).

        Args:
            keep_ratio: Fraction of memories to keep (0.0-1.0).
        """
        memories = self.storage.get_all()
        if not memories:
            return

        total = len(memories)
        keep_count = max(1, int(total * keep_ratio))

        # Sort by importance (highest first)
        memories.sort(key=lambda m: m.importance, reverse=True)

        # Deduplicate near-duplicates among top memories
        keep = []
        for m in memories:
            is_dup = False
            for k in keep:
                if self._similarity(m.content, k.content) > 0.9:
                    is_dup = True
                    break
            if not is_dup:
                keep.append(m)
            if len(keep) >= keep_count:
                break

        # Delete everything not in keep list
        keep_ids = {m.id for m in keep}
        all_ids = {m.id for m in memories}
        to_delete = all_ids - keep_ids

        if to_delete:
            self.storage.delete_by_ids(list(to_delete))

    def _similarity(self, a: str, b: str) -> float:
        """Jaccard similarity for deduplication.

        Uses word-level for languages with spaces (English),
        character bigrams for CJK and other non-spaced scripts.
        """
        if not a or not b:
            return 0.0
        a_lower = a.lower()
        b_lower = b.lower()

        # Word-level sets
        set_a = set(a_lower.split())
        set_b = set(b_lower.split())

        # If word-level gives too few tokens (CJK text without spaces),
        # fall back to character bigrams
        total_words = len(set_a | set_b)
        if total_words <= 2 and len(a_lower) > 5:
            set_a = set(a_lower[i:i+2] for i in range(len(a_lower)-1))
            set_b = set(b_lower[i:i+2] for i in range(len(b_lower)-1))

        if not set_a or not set_b:
            return 0.0
        return len(set_a & set_b) / len(set_a | set_b)
