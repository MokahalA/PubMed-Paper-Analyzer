import re
from typing import Optional
from .cleaner import TextCleaner


class PaperNormalizer:
    """Transform raw PubMed papers into clean, SQLite-ready format."""

    # Medical entity patterns (simple regex-based extraction)
    DISEASE_KEYWORDS = {
        "cancer", "carcinoma", "tumor", "neoplasm", "lymphoma", "leukemia",
        "melanoma", "sarcoma", "adenoma", "glioma", "hpv", "infection",
        "disease", "syndrome", "disorder", "condition", "dysplasia"
    }

    METHOD_KEYWORDS = {
        "deep learning", "machine learning", "neural network", "cnn", "rnn",
        "bert", "transformers", "regression", "classification", "clustering",
        "algorithm", "model", "network", "learning", "training", "ai",
        "artificial intelligence", "convolutional", "recurrent", "lstm"
    }

    ORGAN_KEYWORDS = {
        "lung", "breast", "colon", "liver", "kidney", "pancreas", "brain",
        "prostate", "skin", "stomach", "bone", "blood", "lymph", "anal",
        "cervix", "ovary", "testis", "bladder", "esophagus"
    }

    @staticmethod
    def normalize(raw_paper: dict) -> dict:
        """Transform raw paper dict into clean format."""
        title = raw_paper.get("title") or ""
        abstract = raw_paper.get("abstract") or ""
        combined_text = f"{title} {abstract}"

        # Clean text
        clean_title = TextCleaner.clean_text(title)
        clean_abstract = TextCleaner.clean_text(abstract)

        # Extract entities
        entities = PaperNormalizer._extract_entities(combined_text)

        # Extract keywords
        keywords = TextCleaner.extract_keywords(combined_text, num_keywords=5)

        # Create clean text version (lowercase, normalized)
        clean_text = TextCleaner.normalize_for_comparison(combined_text)

        # Calculate metrics
        abstract_words = len(clean_abstract.split())

        # Build normalized paper
        normalized = {
            "pmid": raw_paper.get("pmid"),
            "title": clean_title,
            "abstract": clean_abstract,
            "authors": raw_paper.get("authors") or [],
            "journal": raw_paper.get("journal") or "",
            "year": PaperNormalizer._extract_year(raw_paper.get("year")),
            "keywords": keywords,
            "entities": entities,
            "clean_text": clean_text,
            "length": {
                "abstract_words": abstract_words,
                "title_words": len(clean_title.split())
            }
        }

        return normalized

    @staticmethod
    def _extract_entities(text: str) -> dict:
        """Extract diseases, methods, organs from text."""
        text_lower = text.lower()

        diseases = PaperNormalizer._find_matches(
            text_lower, PaperNormalizer.DISEASE_KEYWORDS
        )
        methods = PaperNormalizer._find_matches(
            text_lower, PaperNormalizer.METHOD_KEYWORDS
        )
        organs = PaperNormalizer._find_matches(
            text_lower, PaperNormalizer.ORGAN_KEYWORDS
        )

        return {
            "diseases": list(set(diseases)),  # Remove duplicates
            "methods": list(set(methods)),
            "organs": list(set(organs))
        }

    @staticmethod
    def _find_matches(text: str, keywords: set) -> list[str]:
        """Find keyword matches in text."""
        matches = []
        for keyword in keywords:
            # Use word boundary regex for exact word matching
            pattern = rf"\b{re.escape(keyword)}\b"
            if re.search(pattern, text):
                matches.append(keyword)
        return matches

    @staticmethod
    def _extract_year(year_value: Optional[str | int]) -> Optional[int]:
        """Extract year as integer."""
        if not year_value:
            return None

        year_str = str(year_value).strip()

        # Extract 4-digit year
        match = re.search(r"\d{4}", year_str)
        if match:
            try:
                year = int(match.group())
                # Validate reasonable year range
                if 1900 <= year <= 2100:
                    return year
            except ValueError:
                pass

        return None
