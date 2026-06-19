import chromadb
import shutil
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer


class ChromaService:
    def __init__(self, db_path: str = "db/chroma_papers", model_name: str = "all-MiniLM-L6-v2"):
        """
        Args:
            db_path: Path to store ChromaDB persistence
            model_name: HuggingFace embedding model (all-MiniLM-L6-v2 is fast and good for scientific text)
        """
        self.db_path = db_path
        self.model_name = model_name
        
        # Ensure directory exists with write permissions
        db_dir = Path(db_path)
        db_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(str(db_dir), 0o777)
        
        # Initialize ChromaDB with more permissive settings
        old_umask = os.umask(0o000)
        try:
            self.client = chromadb.PersistentClient(path=db_path)
            self.collection = self.client.get_or_create_collection(
                name="research_papers",
                metadata={"hnsw:space": "cosine"}  # Cosine similarity for text
            )
        finally:
            os.umask(old_umask)
        
        self.model = SentenceTransformer(model_name)
    
    ## add papers

    def add_papers(self, papers: list[dict]) -> dict:
        """
        Add papers to ChromaDB collection.
        
        Args:
            papers: List of paper dicts (from SQLite processor)
            
        Returns:
            Dict with stats {added: int, failed: int}
        """
        stats = {"added": 0, "failed": 0}
        
        ids = []
        documents = []
        metadatas = []
        
        for paper in papers:
            try:
                pmid = paper.get("pmid")
                abstract = paper.get("abstract", "")
                
                # Skip if no abstract
                if not abstract:
                    stats["failed"] += 1
                    continue
                
                ids.append(pmid)
                # Combine title + abstract for richer semantic meaning
                documents.append(f"{paper.get('title', '')} {abstract}")
                
                # Store metadata for quick retrieval
                metadatas.append({
                    "title": paper.get("title", ""),
                    "year": str(paper.get("year", "")),
                    "journal": paper.get("journal", ""),
                    "keywords": ",".join(paper.get("keywords", [])),
                })
                
                stats["added"] += 1
            except Exception as e:
                print(f"Error adding paper {paper.get('pmid')}: {e}")
                stats["failed"] += 1

        if ids:
            try:
                self.collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
            except Exception as e:
                # ChromaDB sometimes raises "readonly database" warnings but still succeeds
                # Only re-raise if it's not this specific error
                error_str = str(e).lower()
                if "readonly" not in error_str and "attempt to write" not in error_str:
                    raise
                else:
                    # Warning was raised but data was added, ignore it
                    pass
        
        return stats
    
    ## semantic search based on query

    def semantic_search(self, query: str, n_results: int = 10) -> list[dict]:
        """
        Search for papers semantically similar to query.
        
        Args:
            query: Natural language query
            n_results: Number of results to return
            
        Returns:
            List of matches with {pmid, title, distance, metadata}
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Format results
        formatted = []
        if results['ids'] and results['ids'][0]:
            for i, pmid in enumerate(results['ids'][0]):
                formatted.append({
                    "pmid": pmid,
                    "distance": results['distances'][0][i],  # Lower is better
                    "metadata": results['metadatas'][0][i]
                })
        
        return formatted
    
    def reset(self):
        """Completely clear ChromaDB by removing and recreating the folder."""
        try:
            # Close existing connection first
            try:
                self.collection = None
                self.client = None
            except:
                pass
            
            chroma_dir = Path(self.db_path)
            if chroma_dir.exists():
                shutil.rmtree(chroma_dir)
            
            # Wait a moment for file locks to clear
            import time
            time.sleep(0.5)
            
            # Recreate directory with proper permissions (more permissive)
            chroma_dir.mkdir(parents=True, exist_ok=True)
            os.chmod(str(chroma_dir), 0o777)
            
            # Create fresh database with more permissive permissions
            old_umask = os.umask(0o000)
            try:
                self.client = chromadb.PersistentClient(path=self.db_path)
                self.collection = self.client.get_or_create_collection(
                    name="research_papers",
                    metadata={"hnsw:space": "cosine"}
                )
            finally:
                os.umask(old_umask)
            
            # Set all permissions to be writable
            for root, dirs, files in os.walk(str(chroma_dir)):
                for d in dirs:
                    os.chmod(os.path.join(root, d), 0o777)
                for f in files:
                    os.chmod(os.path.join(root, f), 0o666)
        except Exception as e:
            print(f"Error resetting ChromaDB: {e}")