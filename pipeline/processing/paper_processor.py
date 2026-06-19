from typing import Optional
from .cleaner import TextCleaner
from .normalizer import PaperNormalizer
from .deduplicator import PaperDeduplicator


class PaperProcessor:
    """
    Main processor that handles the complete processing pipeline:
    Raw papers → Clean → Normalize → Deduplicate → SQLite-ready
    """

    def __init__(self, deduplicate: bool = True, similarity_threshold: float = 0.85):
        """
        Args:
            deduplicate: Whether to deduplicate papers
            similarity_threshold: Threshold for deduplication (0-1)
        """
        self.deduplicate_enabled = deduplicate
        self.deduplicator = PaperDeduplicator(similarity_threshold)

    def process(self, raw_papers: list[dict]) -> list[dict]:
        """
        Process a list of raw papers through the full pipeline.

        Args:
            raw_papers: List of raw paper dicts from PubMed API

        Returns:
            List of cleaned, normalized papers ready for SQLite
        """
        # Step 1: Normalize each paper
        normalized_papers = [
            PaperNormalizer.normalize(paper) for paper in raw_papers
        ]

        # Step 2: Deduplicate if enabled
        if self.deduplicate_enabled:
            normalized_papers = self.deduplicator.deduplicate(normalized_papers)

        return normalized_papers


