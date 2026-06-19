"""Retriever service combining ChromaDB semantic search with SQLite metadata filtering."""

from db.repository import PaperRepository
from pipeline.embedding.chroma_service import ChromaService


class Retriever:
    """Combine semantic search with structured metadata filtering."""
    
    def __init__(self):
        self.db_repo = PaperRepository()
        self.chroma = ChromaService()
    
    def search(
        self, 
        query: str, 
        top_k: int = 10,
        year_from: int = None,
        year_to: int = None,
        journal: str = None
    ) -> list[dict]:
        """
        Search for papers using semantic similarity and optional filters.
        
        Args:
            query: Natural language query
            top_k: Number of results to return
            year_from: Filter papers from year (inclusive)
            year_to: Filter papers to year (inclusive)
            journal: Filter by journal name
        
        Returns:
            List of papers sorted by relevance with full details
        """
        # Step 1: Semantic search via ChromaDB
        semantic_results = self.chroma.semantic_search(query, n_results=top_k * 2)
        
        if not semantic_results:
            return []
        
        # Step 2: Fetch full paper details from SQLite
        papers_with_details = []
        for result in semantic_results:
            pmid = result['pmid']
            paper = self.db_repo.get_by_pmid(pmid)
            
            if paper:
                paper['relevance_score'] = 1 - result['distance']  # Convert distance to similarity
                papers_with_details.append(paper)
        
        # Step 3: Apply metadata filters
        filtered = self._apply_filters(
            papers_with_details,
            year_from=year_from,
            year_to=year_to,
            journal=journal
        )
        
        # Step 4: Sort by relevance and return top_k
        sorted_papers = sorted(
            filtered,
            key=lambda p: p.get('relevance_score', 0),
            reverse=True
        )
        
        return sorted_papers[:top_k]
    
    def _apply_filters(self, papers: list[dict], **filters) -> list[dict]:
        """Apply metadata filters to papers."""
        filtered = papers
        
        if filters.get('year_from'):
            filtered = [
                p for p in filtered
                if p.get('year') and p['year'] >= filters['year_from']
            ]
        
        if filters.get('year_to'):
            filtered = [
                p for p in filtered
                if p.get('year') and p['year'] <= filters['year_to']
            ]
        
        if filters.get('journal'):
            journal_filter = filters['journal'].lower()
            filtered = [
                p for p in filtered
                if p.get('journal', '').lower() == journal_filter
            ]
        
        return filtered
    
    def get_paper_details(self, pmid: str) -> dict:
        """Get full details of a paper by PMID."""
        return self.db_repo.get_by_pmid(pmid)
