import json
import os
from datetime import datetime
from pathlib import Path

from .pubmed_client import PubMedClient
from .pubmed_parser import PubMedParser


class PubMedService:
    def __init__(self, data_raw_dir: str = "data/raw"):
        self.client = PubMedClient()
        self.parser = PubMedParser()
        self.data_raw_dir = Path(data_raw_dir)
        self.data_raw_dir.mkdir(parents=True, exist_ok=True)

    def get_papers(self, query: str, max_results: int = 10) -> list[dict]:
        """
        Full pipeline with file storage:
        query → get pmids → xml → structured papers
        Raw JSON stored under data/raw/
        """
        # Search and save raw search results
        pmids = self.client.search(query, max_results)
        self._save_search_results(query, pmids, max_results)

        # Fetch XML data
        xml_data = self.client.fetch(pmids)
        self._save_raw_xml(query, xml_data)

        # Parse and save structured papers
        papers = self.parser.parse(xml_data)
        self._save_parsed_papers(query, papers)

        return papers

    def _save_search_results(self, query: str, pmids: list[str], max_results: int) -> None:
        """Save raw search results as JSON"""
        filename = self._get_timestamp_filename("search_results")
        filepath = self.data_raw_dir / filename

        data = {
            "query": query,
            "max_results": max_results,
            "pmids_count": len(pmids),
            "pmids": pmids,
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def _save_raw_xml(self, query: str, xml_data: str) -> None:
        """Save raw XML response from PubMed"""
        filename = self._get_timestamp_filename("raw_xml", ext=".xml")
        filepath = self.data_raw_dir / filename

        with open(filepath, "w") as f:
            f.write(xml_data)

    def _save_parsed_papers(self, query: str, papers: list[dict]) -> None:
        """Save parsed and structured papers as JSON"""
        filename = self._get_timestamp_filename("parsed_papers")
        filepath = self.data_raw_dir / filename

        data = {
            "query": query,
            "papers_count": len(papers),
            "papers": papers,
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def _get_timestamp_filename(self, prefix: str, ext: str = ".json") -> str:
        """Generate filename with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}{ext}"
    
