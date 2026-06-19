"""Flask backend API for Healthcare Research Analyzer."""

import sys
from pathlib import Path

# Add project root to path so we can import pipeline
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask, request, jsonify
from pipeline.rag.rag_service import RAGService
from pipeline.retrieval.retriever import Retriever
from pipeline.service import PipelineService
from pipeline.ingestion.pubmed_service import PubMedService

app = Flask(__name__)

# Initialize services
rag_service = RAGService()
retriever = Retriever()
pipeline_service = PipelineService()
pubmed_service = PubMedService()


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200


@app.route('/api/ingest', methods=['POST'])
def ingest():
    """
    Ingest papers from PubMed based on user query.
    
    Request body:
    {
        "query": "cancer immunotherapy",
        "max_results": 50
    }
    """
    try:
        data = request.json
        query = data.get('query')
        max_results = data.get('max_results', 50)
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        # Fetch papers from PubMed
        raw_papers = pubmed_service.get_papers(query, max_results=max_results)
        
        if not raw_papers:
            return jsonify({"error": "No papers found for this query"}), 404
        
        # Process and store in both SQLite and ChromaDB
        stats = pipeline_service.process_and_store(raw_papers)
        
        return jsonify({
            "message": f"Successfully ingested papers for query: {query}",
            "stats": stats,
            "query": query,
            "max_results": max_results
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/search', methods=['POST'])
def search():
    """
    Search for papers without RAG (just retrieval + metadata).
    
    Request body:
    {
        "query": "immunotherapy cancer",
        "top_k": 10,
        "year_from": 2020,
        "year_to": 2026
    }
    """
    try:
        data = request.json
        query = data.get('query')
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        top_k = data.get('top_k', 10)
        year_from = data.get('year_from')
        year_to = data.get('year_to')
        
        papers = retriever.search(
            query=query,
            top_k=top_k,
            year_from=year_from,
            year_to=year_to
        )
        
        return jsonify({
            "papers": papers,
            "count": len(papers)
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/ask', methods=['POST'])
def ask():
    """
    Answer a question using RAG, optionally with selected papers.
    
    Request body (option 1 - auto-retrieve):
    {
        "question": "What are advances in cancer immunotherapy?",
        "top_k": 5,
        "year_from": 2020,
        "year_to": 2026
    }
    
    Request body (option 2 - use selected papers):
    {
        "question": "What are advances in cancer immunotherapy?",
        "selected_paper_ids": ["12345", "67890"]
    }
    """
    try:
        data = request.json
        question = data.get('question')
        
        if not question:
            return jsonify({"error": "Question is required"}), 400
        
        selected_paper_ids = data.get('selected_paper_ids')
        
        # If specific papers are selected, use only those
        if selected_paper_ids:
            result = rag_service.answer_with_papers(
                question=question,
                paper_ids=selected_paper_ids,
                include_sources=True
            )
        else:
            # Otherwise, retrieve papers automatically
            top_k = data.get('top_k', 5)
            year_from = data.get('year_from')
            year_to = data.get('year_to')
            
            result = rag_service.answer(
                question=question,
                top_k=top_k,
                year_from=year_from,
                year_to=year_to,
                include_sources=True
            )
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/papers', methods=['GET'])
def get_all_papers():
    """Get all papers in the database."""
    try:
        from db.repository import PaperRepository
        repo = PaperRepository()
        papers = repo.get_all()
        
        return jsonify({
            "papers": papers,
            "count": len(papers)
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/papers/<pmid>', methods=['GET'])
def get_paper(pmid):
    """Get full details of a paper by PMID."""
    try:
        paper = retriever.get_paper_details(pmid)
        
        if not paper:
            return jsonify({"error": f"Paper {pmid} not found"}), 404
        
        return jsonify(paper), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/papers/<pmid>', methods=['DELETE'])
def delete_paper(pmid):
    """Delete a paper by PMID."""
    try:
        from db.repository import PaperRepository
        repo = PaperRepository()
        repo.delete_by_pmid(pmid)
        
        return jsonify({"message": f"Paper {pmid} deleted successfully"}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/papers/batch/delete', methods=['POST'])
def delete_papers_batch():
    """Delete multiple papers by PMID."""
    try:
        data = request.json
        pmids = data.get('pmids', [])
        
        if not pmids:
            return jsonify({"error": "No PMIDs provided"}), 400
        
        from db.repository import PaperRepository
        repo = PaperRepository()
        
        for pmid in pmids:
            repo.delete_by_pmid(pmid)
        
        return jsonify({
            "message": f"Deleted {len(pmids)} papers",
            "deleted": len(pmids)
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
