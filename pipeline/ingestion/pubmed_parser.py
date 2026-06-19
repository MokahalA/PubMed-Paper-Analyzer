# pipeline/pubmed_parser.py

import xml.etree.ElementTree as ET


class PubMedParser:
    def parse(self, xml_data: str) -> list[dict]:
        """
        Convert PubMed XML into structured Python dictionaries
        """
        if not xml_data:
            return []

        root = ET.fromstring(xml_data)
        papers = []

        for article in root.findall(".//PubmedArticle"):

            pmid = article.findtext(".//PMID")
            title = article.findtext(".//ArticleTitle")

            # Abstract may have multiple parts → join them
            abstract_parts = article.findall(".//AbstractText")
            abstract = " ".join(
                [part.text for part in abstract_parts if part.text]
            )

            # Year extraction (PubMed is messy here)
            year = (
                article.findtext(".//PubDate/Year")
                or article.findtext(".//MedlineDate")
            )

            # Authors
            authors = [
                a.findtext("LastName") + " " + (a.findtext("ForeName") or "")
                for a in article.findall(".//Author")
                if a.findtext("LastName")
            ]

            papers.append({
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "year": year,
                "authors": authors,
            })

        return papers