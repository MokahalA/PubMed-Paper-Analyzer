from typing import Optional
from .cleaner import TextCleaner
from difflib import SequenceMatcher


class PaperDeduplicator:
    """Remove duplicate papers from a list."""

    def __init__(self, similarity_threshold: float = 0.85):
        """
        Args:
            similarity_threshold: Minimum similarity (0-1) to consider papers duplicates
        """
        self.similarity_threshold = similarity_threshold

    def deduplicate(self, papers: list[dict]) -> list[dict]:
        """
        Remove duplicate papers, keeping the first occurrence.
        Returns list of unique papers.
        """
        seen_pmids = set()
        seen_normalized_titles = set()
        unique_papers = []

        for paper in papers:
            pmid = paper.get("pmid")

            # Skip if PMID already seen
            if pmid and pmid in seen_pmids:
                continue

            # Normalize title for comparison
            title = paper.get("title", "")
            normalized_title = TextCleaner.normalize_for_comparison(title)

            # Check for similar titles
            is_duplicate = False
            for seen_title in seen_normalized_titles:
                similarity = self._calculate_similarity(normalized_title, seen_title)
                if similarity >= self.similarity_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_papers.append(paper)
                if pmid:
                    seen_pmids.add(pmid)
                seen_normalized_titles.add(normalized_title)

        return unique_papers

    @staticmethod
    def _calculate_similarity(text1: str, text2: str) -> float:
        """Calculate string similarity using SequenceMatcher (0-1)."""
        if not text1 or not text2:
            return 0.0

        matcher = SequenceMatcher(None, text1, text2)
        return matcher.ratio()
