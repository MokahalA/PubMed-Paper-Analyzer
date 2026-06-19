import argparse
import json
from pathlib import Path
from pipeline.ingestion.pubmed_service import PubMedService
from pipeline.service import PipelineService
from pipeline.utils.cleanup import CleanupService


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test the healthcare research analyzer pipeline")
    parser.add_argument("--reset", action="store_true", help="Reset database and embeddings before running")
    args = parser.parse_args()
    
    # Reset if requested
    if args.reset:
        cleanup = CleanupService()
        cleanup.reset_all()

    # Step 1: Ingest papers from PubMed
    print("Ingesting papers from PubMed...")
    service = PubMedService()
    raw_papers = service.get_papers("machine learning uses in heart disease", max_results=10)
    print(f"Retrieved {len(raw_papers)} raw papers\n")

    # Step 2-3: Process and store to both SQLite and ChromaDB
    print("🔄 Processing and storing papers...")
    pipeline = PipelineService()
    stats = pipeline.process_and_store(raw_papers)
    
    print(f"✅ Pipeline complete!")
    print(f"   Input papers: {len(raw_papers)}")
    print(f"   After processing: {stats['processed']}")
    print(f"   Papers with abstracts: {stats['papers_with_abstracts']}")
    print(f"   Skipped (no abstract): {stats['skipped_no_abstract']}")
    print(f"\n Database storage:")
    print(f"   Inserted: {stats['database']['inserted']}")
    print(f"   Updated: {stats['database']['updated']}")
    print(f"   Failed: {stats['database']['failed']}")
    print(f"\n ChromaDB embeddings:")
    print(f"   Added: {stats['embeddings']['added']}")
    print(f"   Failed: {stats['embeddings']['failed']}\n")


if __name__ == "__main__":
    main()