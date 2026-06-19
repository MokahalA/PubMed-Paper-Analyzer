"""RAG (Retrieval-Augmented Generation) service for answering healthcare research questions."""

from pipeline.retrieval.retriever import Retriever


class RAGService:
    """Answer questions using retrieved papers and an LLM."""
    
    def __init__(self, llm=None):
        """
        Args:
            llm: Language model to use (default: Ollama with mistral)
        """
        self.retriever = Retriever()
        
        if llm is None:
            # Import here to avoid hard dependency if not using RAG
            try:
                from langchain_community.llms.ollama import Ollama
                self.llm = Ollama(model="gemma3:4b")
            except ImportError:
                raise ImportError(
                    "LangChain not installed. Install with: pip install langchain langchain-community"
                )
        else:
            self.llm = llm
    
    def answer(
        self,
        question: str,
        top_k: int = 5,
        year_from: int = None,
        year_to: int = None,
        include_sources: bool = True
    ) -> dict:
        """
        Answer a healthcare research question using RAG.
        
        Args:
            question: The user's question
            top_k: Number of papers to retrieve
            year_from: Filter papers from year
            year_to: Filter papers to year
            include_sources: Include retrieved papers in response
        
        Returns:
            Dict with {answer: str, sources: list, metadata: dict}
        """
        # Step 1: Retrieve relevant papers
        retrieved_papers = self.retriever.search(
            query=question,
            top_k=top_k,
            year_from=year_from,
            year_to=year_to
        )
        
        if not retrieved_papers:
            return {
                "answer": "No relevant papers found for your question.",
                "sources": [],
                "metadata": {"num_papers": 0}
            }
        
        # Step 2: Build context from papers
        context = self._build_context(retrieved_papers)
        
        # Step 3: Generate answer using LLM
        prompt = self._build_prompt(question, context)
        answer = self.llm.invoke(prompt)
        
        # Step 4: Format response
        return {
            "answer": answer,
            "sources": [
                {
                    "pmid": p.get('pmid'),
                    "title": p.get('title'),
                    "year": p.get('year'),
                    "relevance": round(p.get('relevance_score', 0), 3)
                }
                for p in retrieved_papers
            ] if include_sources else [],
            "metadata": {
                "num_papers": len(retrieved_papers),
                "years": {
                    "from": year_from,
                    "to": year_to
                }
            }
        }
    
    def answer_with_papers(
        self,
        question: str,
        paper_ids: list[str],
        include_sources: bool = True
    ) -> dict:
        """
        Answer a question based on user-selected papers.
        
        Args:
            question: The user's question
            paper_ids: List of PMIDs to use for answering
            include_sources: Include papers in response
        
        Returns:
            Dict with {answer: str, sources: list, metadata: dict}
        """
        from db.repository import PaperRepository
        
        repo = PaperRepository()
        
        # Fetch selected papers from database
        selected_papers = []
        for pmid in paper_ids:
            paper = repo.get_by_pmid(pmid)
            if paper:
                selected_papers.append(paper)
        
        if not selected_papers:
            return {
                "answer": "No papers found for the selected IDs.",
                "sources": [],
                "metadata": {"num_papers": 0}
            }
        
        # Build context from selected papers
        context = self._build_context(selected_papers)
        
        # Generate answer using LLM
        prompt = self._build_prompt(question, context)
        answer = self.llm.invoke(prompt)
        
        # Format response
        return {
            "answer": answer,
            "sources": [
                {
                    "pmid": p.get('pmid'),
                    "title": p.get('title'),
                    "year": p.get('year'),
                    "relevance": 1.0  # User selected, so perfect relevance
                }
                for p in selected_papers
            ] if include_sources else [],
            "metadata": {
                "num_papers": len(selected_papers),
                "selection_mode": "user-selected"
            }
        }
    
    def _build_context(self, papers: list[dict]) -> str:
        """Build context string from retrieved papers."""
        context_parts = []
        
        for i, paper in enumerate(papers, 1):
            part = f"""
Paper {i}: {paper.get('title', 'N/A')}
Authors: {', '.join(paper.get('authors', []))}
Year: {paper.get('year', 'N/A')}
Journal: {paper.get('journal', 'N/A')}
Abstract: {paper.get('abstract', 'N/A')}
---
"""
            context_parts.append(part)
        
        return "\n".join(context_parts)
    
    def _build_prompt(self, question: str, context: str) -> str:
        """Build the prompt for the LLM."""
        prompt = f"""You are an expert healthcare researcher. Based on the following research papers, answer the user's question.

RESEARCH PAPERS:
{context}

QUESTION:
{question}

INSTRUCTIONS:
1. Answer based primarily on the provided papers
2. Be specific and cite findings from the papers
3. If the papers don't contain enough information, say so
4. Maintain scientific accuracy

ANSWER:"""
        
        return prompt
