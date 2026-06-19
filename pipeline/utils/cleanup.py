"""Cleanup and reset functionality for testing."""

import shutil
import os
from pathlib import Path
from db.repository import PaperRepository
from ..embedding.chroma_service import ChromaService


class CleanupService:
    """Manage cleanup of cached data and test artifacts."""
    
    def __init__(self):
        self.db_repo = PaperRepository()
        self.chroma = ChromaService()
    
    def _set_dir_permissions(self, path: Path):
        """Recursively set proper permissions on directory and contents."""
        if path.exists():
            os.chmod(str(path), 0o755)
            for root, dirs, files in os.walk(str(path)):
                for d in dirs:
                    os.chmod(os.path.join(root, d), 0o755)
                for f in files:
                    os.chmod(os.path.join(root, f), 0o644)
    
    def reset_database(self):
        """Clear SQLite database."""
        try:
            # Delete database file if it exists
            db_path = Path("db/research_papers.db")
            if db_path.exists():
                db_path.unlink()
            
            # Delete WAL files (Write-Ahead Log)
            wal_path = Path("db/research_papers.db-wal")
            shm_path = Path("db/research_papers.db-shm")
            if wal_path.exists():
                wal_path.unlink()
            if shm_path.exists():
                shm_path.unlink()
            
            # Recreate db directory with proper permissions
            db_dir = Path("db")
            db_dir.mkdir(parents=True, exist_ok=True)
            self._set_dir_permissions(db_dir)
            
            # Reinitialize schema
            from db.schema import init_db
            init_db()
            
            print("  ✅ Database cleared and reinitialized")
        except Exception as e:
            print(f"  ⚠️ Error during database reset: {e}")
    
    def reset_embeddings(self):
        """Clear ChromaDB collection."""
        try:
            self.chroma.reset()
            chroma_dir = Path(self.chroma.db_path)
            self._set_dir_permissions(chroma_dir)
            print("  ✅ ChromaDB cleared")
        except Exception as e:
            print(f"  ⚠️ Error during embeddings reset: {e}")
    
    def reset_raw_data(self):
        """Clear raw ingestion files."""
        raw_dir = Path("data/raw")
        if raw_dir.exists():
            shutil.rmtree(raw_dir)
        raw_dir.mkdir(parents=True, exist_ok=True)
        self._set_dir_permissions(raw_dir)
        print("  ✅ Raw data cleared")
    
    def reset_all(self):
        """Full cleanup - start from scratch."""
        print("\n🧹 Resetting pipeline...\n")
        self.reset_database()
        self.reset_embeddings()
        self.reset_raw_data()
        print("\n✅ Pipeline reset complete\n")
