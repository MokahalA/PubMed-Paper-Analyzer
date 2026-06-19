"""Main orchestrator for the data pipeline."""

from .processing.paper_processor import PaperProcessor
from .embedding.chroma_service import ChromaService
from db.repository import PaperRepository


class PipelineService:
    """Orchestrate processing to both SQLite and ChromaDB."""
    
    def __init__(self):
        self.db_repo = PaperRepository()
        self.chroma = ChromaService()
    
    def process_and_store(self, raw_papers: list[dict]) -> dict:
        """
        Process papers and store in both SQLite and ChromaDB.
        
        Args:
            raw_papers: List of raw paper dicts from PubMed API
        
        Returns:
            Stats dict with all operations
        """
        # Process papers (existing logic)
        processor = PaperProcessor(deduplicate=True)
        processed = processor.process(raw_papers)
        
        # Filter out papers without abstracts
        papers_with_abstracts = [
            p for p in processed 
            if p.get("abstract", "").strip()
        ]
        
        skipped_count = len(processed) - len(papers_with_abstracts)
        
        # Store in SQLite
        db_stats = self.db_repo.insert_batch(papers_with_abstracts)
        
        # Store in ChromaDB
        chroma_stats = self.chroma.add_papers(papers_with_abstracts)
        
        return {
            "processed": len(processed),
            "papers_with_abstracts": len(papers_with_abstracts),
            "skipped_no_abstract": skipped_count,
            "database": db_stats,
            "embeddings": chroma_stats
        }
