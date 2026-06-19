# pipeline/pubmed_client.py

import requests


class PubMedClient:
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def search(self, query: str, max_results: int = 10) -> list[str]:
        """
        Step 1: Search PubMed and return list of PMIDs
        """
        response = requests.get(
            f"{self.BASE_URL}/esearch.fcgi",
            params={
                "db": "pubmed",
                "term": query,
                "retmode": "json",
                "retmax": max_results,
            },
            timeout=10,
        )

        response.raise_for_status()
        data = response.json()

        return data["esearchresult"]["idlist"]

    def fetch(self, pmids: list[str]) -> str:
        """
        Step 2: Fetch full article data as XML
        """
        if not pmids:
            return ""

        response = requests.get(
            f"{self.BASE_URL}/efetch.fcgi",
            params={
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
            },
            timeout=10,
        )

        response.raise_for_status()
        return response.text