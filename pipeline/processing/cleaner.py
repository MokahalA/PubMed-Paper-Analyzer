import re
import string
from typing import Optional


class TextCleaner:
    """Clean and normalize text from papers."""

    @staticmethod
    def clean_text(text: Optional[str]) -> str:
        """
        Clean and normalize text:
        - Remove extra whitespace
        - Handle special characters
        - Convert to lowercase for processing
        """
        if not text:
            return ""

        # Remove extra whitespace
        text = " ".join(text.split())

        # Remove special characters but keep common punctuation
        text = re.sub(r"[\u2009\u00A0]", " ", text)  # Remove non-breaking spaces

        return text.strip()

    @staticmethod
    def normalize_for_comparison(text: Optional[str]) -> str:
        """Normalize text for deduplication/comparison."""
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove punctuation and extra spaces
        text = re.sub(f"[{re.escape(string.punctuation)}]", "", text)
        text = " ".join(text.split())

        return text.strip()

    @staticmethod
    def extract_keywords(text: Optional[str], num_keywords: int = 5) -> list[str]:
        """
        Extract keywords from text using simple heuristics.
        - Long words (5+ chars)
        - Frequent terms
        """
        if not text:
            return []

        # Split into words and filter
        words = text.lower().split()
        keywords = [
            w.strip(string.punctuation)
            for w in words
            if len(w) >= 5 and w.lower() not in _STOPWORDS
        ]

        # Return top frequent keywords
        from collections import Counter

        counter = Counter(keywords)
        return [word for word, _ in counter.most_common(num_keywords)]


# Common stopwords for medical texts
_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "can", "this", "that", "these",
    "those", "i", "you", "he", "she", "it", "we", "they", "what", "which",
    "who", "when", "where", "why", "how", "all", "each", "every", "both",
    "few", "more", "most", "other", "some", "such", "no", "nor", "not",
    "only", "same", "so", "than", "too", "very", "just", "also", "background"
}
