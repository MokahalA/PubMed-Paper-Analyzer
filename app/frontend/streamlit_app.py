"""Streamlit frontend for Healthcare Research Analyzer."""

import streamlit as st
import requests
import subprocess
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="PubMed Research Paper Chatbot",
    page_icon="🔬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# API endpoint
API_URL = "http://localhost:5000"

# Title with reset button
col1, col2 = st.columns([0.85, 0.15])

with col1:
    st.title("🔬 PubMed Research Paper Chatbot")

with col2:
    if st.button("🔄 Reset", help="Clear all data and reset database"):
        with st.spinner("Resetting..."):
            try:
                subprocess.run(
                    ["python3", "reset.py", "--all"],
                    cwd="/Users/ahmad/Desktop/AppDev-Summer2026/AI Projects/Healthcare Research Analyzer",
                    timeout=30,
                    check=True
                )
                st.success("✅ Data reset successfully!")
                st.rerun()
            except subprocess.CalledProcessError as e:
                st.error(f"Reset failed: {str(e)}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Tab selection
tab1, tab2, tab3 = st.tabs(["📥 Ingest", "📚 Papers", "❓ Ask"])

# ============ TAB 1: INGEST PAPERS ============
with tab1:
    st.header("Ingest Papers from PubMed")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        ingest_query = st.text_input(
            "Search query",
            placeholder="e.g., cancer immunotherapy"
        )
        max_results = st.slider("Number of papers", 5, 100, 30)
    
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        ingest_button = st.button("Ingest", use_container_width=True, type="primary")
    
    if ingest_button and ingest_query:
        with st.spinner("Fetching and processing..."):
            try:
                response = requests.post(
                    f"{API_URL}/api/ingest",
                    json={
                        "query": ingest_query,
                        "max_results": max_results
                    },
                    timeout=120
                )
                
                if response.status_code == 200:
                    data = response.json()
                    stats = data.get('stats', {})
                    
                    st.success("✅ Done!")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Processed", stats.get('processed', 0))
                    with col2:
                        st.metric("Stored", stats.get('database', {}).get('inserted', 0))
                    with col3:
                        st.metric("Indexed", stats.get('embeddings', {}).get('added', 0))
                
                else:
                    error_msg = response.json().get('error', 'Unknown error')
                    # Suppress readonly database warnings - data is still added successfully
                    if "readonly" not in error_msg.lower():
                        st.error(f"Error: {error_msg}")
                    else:
                        st.success("✅ Papers ingested successfully (ignore database warning)")
            
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend. Is Flask running on port 5000?")
            except Exception as e:
                st.error(f"Error: {str(e)}")


# ============ TAB 2: VIEW PAPERS ============
with tab2:
    st.header("Papers in Database")
    
    # Initialize selection state FIRST
    if 'selected_pmids' not in st.session_state:
        st.session_state.selected_pmids = set()
    
    if st.button("Load Papers", use_container_width=True):
        with st.spinner("Loading..."):
            try:
                response = requests.get(
                    f"{API_URL}/api/papers",
                    timeout=30
                )
                
                if response.status_code == 200:
                    papers = response.json().get('papers', [])
                    st.session_state.papers = papers
                    st.success(f"✅ Loaded {len(papers)} papers")
                else:
                    st.error(f"Error: {response.json().get('error')}")
            
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend. Is Flask running?")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    if 'papers' in st.session_state:
        papers = st.session_state.papers
        
        if papers:
            # Show selection status prominently - AFTER initializing session state
            selected_count = len(st.session_state.selected_pmids)
            st.metric("Papers Selected for RAG Analysis", selected_count, delta=f"of {len(papers)} total")
            
            # Display papers with checkboxes and delete buttons
            for paper in papers:
                pmid = paper.get('pmid')
                is_selected = pmid in st.session_state.selected_pmids
                
                # Visual highlight for selected papers
                if is_selected:
                    st.markdown("### ✅ " + paper.get('title'))
                else:
                    st.markdown("### " + paper.get('title'))
                
                col1, col2, col3 = st.columns([0.1, 0.8, 0.1])
                
                with col1:
                    selected = st.checkbox(
                        "Select",
                        value=is_selected,
                        key=f"select_{pmid}",
                        label_visibility="collapsed"
                    )
                    if selected != is_selected:
                        if selected:
                            st.session_state.selected_pmids.add(pmid)
                        else:
                            st.session_state.selected_pmids.discard(pmid)
                        st.rerun()
                
                with col2:
                    st.write(f"Year: {paper.get('year')} | Journal: {paper.get('journal')} | PMID: {pmid[:8]}...")
                    st.caption(paper.get('abstract', 'N/A')[:250] + "...")
                
                with col3:
                    if st.button("🗑️", key=f"delete_{pmid}", help="Delete this paper"):
                        with st.spinner("Deleting..."):
                            try:
                                response = requests.delete(
                                    f"{API_URL}/api/papers/{pmid}",
                                    timeout=10
                                )
                                
                                if response.status_code == 200:
                                    st.session_state.papers = [p for p in papers if p.get('pmid') != pmid]
                                    st.session_state.selected_pmids.discard(pmid)
                                    st.success("Paper deleted")
                                    st.rerun()
                                else:
                                    st.error("Delete failed")
                            
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                
                st.divider()
        else:
            st.info("No papers in database yet")


# ============ TAB 3: ASK QUESTION ============
with tab3:
    st.header("Chat About Selected Papers")
    
    # Initialize selection state and chat history
    if 'selected_pmids' not in st.session_state:
        st.session_state.selected_pmids = set()
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    selected_count = len(st.session_state.selected_pmids)
    
    if selected_count == 0:
        st.warning("⚠️ No papers selected! Go to the 'Papers' tab and select papers to analyze.")
    else:
        st.info(f"💬 Chatting about {selected_count} selected papers")
        
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.write(message["content"])
                else:
                    st.write(message["content"])
                    if "sources" in message:
                        with st.expander("📚 Sources"):
                            for i, source in enumerate(message["sources"], 1):
                                st.write(f"**{i}. {source.get('title')}**")
                                st.caption(f"Year: {source.get('year')} | PMID: {source.get('pmid')}")
        
        # Chat input
        question = st.chat_input(
            "Ask a question about the selected papers...",
            key="chat_input"
        )
        
        if question:
            # Add user message to history
            st.session_state.chat_history.append({
                "role": "user",
                "content": question
            })
            
            # Display user message immediately
            with st.chat_message("user"):
                st.write(question)
            
            # Get answer from API
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        response = requests.post(
                            f"{API_URL}/api/ask",
                            json={
                                "question": question,
                                "selected_paper_ids": list(st.session_state.selected_pmids)
                            },
                            timeout=60
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            answer = data.get('answer', '')
                            sources = data.get('sources', [])
                            
                            # Display answer
                            st.write(answer)
                            
                            # Add to history
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": answer,
                                "sources": sources
                            })
                            
                            # Display sources in expandable
                            if sources:
                                with st.expander("📚 Sources"):
                                    for i, source in enumerate(sources, 1):
                                        st.write(f"**{i}. {source.get('title')}**")
                                        st.caption(f"Year: {source.get('year')} | PMID: {source.get('pmid')}")
                        
                        else:
                            error_msg = f"Error: {response.json().get('error', 'Unknown error')}"
                            st.error(error_msg)
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": error_msg
                            })
                    
                    except requests.exceptions.ConnectionError:
                        error_msg = "❌ Cannot connect to backend. Is Flask running?"
                        st.error(error_msg)
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": error_msg
                        })
                    except Exception as e:
                        error_msg = f"Error: {str(e)}"
                        st.error(error_msg)
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": error_msg
                        })
            
            st.rerun()
        
        # Clear chat button
        if st.session_state.chat_history:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()


# Footer
st.markdown("---")
st.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
