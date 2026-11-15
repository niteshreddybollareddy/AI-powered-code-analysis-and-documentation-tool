# app.py
import streamlit as st
import os
import shutil
from datetime import datetime
from code_loader import clone_repository, get_code_files
from code_chunker import chunk_code_files
from vector_store import create_vector_store, load_vector_store
from rag_chain import create_rag_chain
from cache_manager import get_cache_manager, check_repo_cache, update_repo_cache
from export_utils import create_export_ui
from logger import get_logger, log_app_start, log_repo_indexing_start, log_repo_indexing_complete, log_query, log_error, log_cache_hit, log_cache_miss

# --- App Configuration ---
st.set_page_config(page_title="Codebase Oracle", layout="wide")
st.title("🤖 Codebase Oracle: Ask Questions About Any GitHub Repo")

# Initialize logging
log_app_start()

# --- Cache Statistics ---
cache_manager = get_cache_manager()
cache_stats = cache_manager.get_cache_stats()

if cache_stats['cached_repositories'] > 0:
    with st.expander("📊 Cache Statistics", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Cached Repos", cache_stats['cached_repositories'])
        with col2:
            st.metric("Total Files", cache_stats['total_files'])
        with col3:
            st.metric("Total Chunks", cache_stats['total_chunks'])
        with col4:
            st.metric("Languages", len(cache_stats['language_breakdown']))

        # Show recent repositories
        recent_repos = cache_manager.get_recent_repos(3)
        if recent_repos:
            st.subheader("🕒 Recently Indexed")
            for repo in recent_repos:
                st.write(f"• **{repo.get('repo_name', 'Unknown')}** - {repo.get('file_count', 0)} files")

# --- Constants ---
REPO_DIR = "temp_repo"
DB_DIR = "chroma_db_code"

# --- State Management ---
# Using session_state to store the chain and retriever
if 'rag_chain' not in st.session_state:
    st.session_state.rag_chain = None
if 'retriever' not in st.session_state:
    st.session_state.retriever = None

# --- UI Components ---
repo_url = st.text_input("Enter a GitHub Repository URL to analyze:", placeholder="https://github.com/pallets/flask")

if st.button("Index Repository"):
    if not repo_url:
        st.warning("Please enter a repository URL.")
    else:
        # Check cache first
        is_cached, cache_info = check_repo_cache(repo_url)

        if is_cached and cache_info:
            # Load from cache
            log_cache_hit(repo_url)
            with st.spinner("Loading cached repository..."):
                try:
                    db = load_vector_store(persist_directory=cache_info['db_path'])
                    retriever = db.as_retriever(search_kwargs={"k": 5})
                    st.session_state.retriever = retriever  # Store retriever for keyword search
                    st.session_state.rag_chain = create_rag_chain(retriever)

                    st.success("✅ Repository loaded from cache!")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Files Cached", cache_info.get('file_count', 0))
                    with col2:
                        st.metric("Chunks Cached", cache_info.get('chunk_count', 0))
                    with col3:
                        st.metric("Languages", len(cache_info.get('languages', {})))

                    st.info("🎉 You can now ask questions about the codebase!")
                    # Repository loaded from cache successfully
                except Exception as e:
                    log_error(e, "cache_loading")
                    st.warning(f"Cache loading failed: {e}. Re-indexing repository...")
                    # Fall through to full indexing
        else:
            log_cache_miss(repo_url)

        # Create progress tracking elements
        progress_bar = st.progress(0)
        status_text = st.empty()
        details_text = st.empty()

        try:
            # Log indexing start
            log_repo_indexing_start(repo_url)

            # Step 1: Clean up old files
            status_text.text("🧹 Cleaning up previous data...")
            progress_bar.progress(5)

            if os.path.exists(REPO_DIR):
                shutil.rmtree(REPO_DIR)
            if os.path.exists(DB_DIR):
                shutil.rmtree(DB_DIR)

            # Step 2: Clone repository
            status_text.text("📥 Cloning repository...")
            progress_bar.progress(15)
            details_text.text("This may take a moment for large repositories...")

            clone_repository(repo_url, REPO_DIR)

            # Step 3: Discover code files
            status_text.text("🔍 Discovering code files...")
            progress_bar.progress(25)

            code_files = get_code_files(REPO_DIR)

            if not code_files:
                st.error("No code files found in the repository. Check the URL or file extensions.")
                progress_bar.empty()
                status_text.empty()
                details_text.empty()
                # No files found, stopping indexing process

            # Show file statistics
            file_stats = {}
            for file_path in code_files:
                ext = os.path.splitext(file_path)[1].lower()
                file_stats[ext] = file_stats.get(ext, 0) + 1

            details_text.text(f"Found {len(code_files)} files: {', '.join([f'{count} {ext}' for ext, count in file_stats.items()])}")

            # Step 4: Chunk code with progress tracking
            status_text.text("✂️ Processing and chunking code...")
            progress_bar.progress(40)

            def chunking_progress_callback(message):
                details_text.text(message)

            documents = chunk_code_files(code_files, progress_callback=chunking_progress_callback)

            # Show chunking statistics
            language_stats = {}
            for doc in documents:
                lang = doc.metadata.get('language', 'unknown')
                language_stats[lang] = language_stats.get(lang, 0) + 1

            progress_bar.progress(70)
            details_text.text(f"Created {len(documents)} chunks from {len(language_stats)} languages: {', '.join([f'{lang}: {count}' for lang, count in language_stats.items()])}")

            # Step 5: Create vector store
            status_text.text("🧮 Creating vector embeddings...")
            progress_bar.progress(85)

            db = create_vector_store(documents, persist_directory=DB_DIR)
            retriever = db.as_retriever(search_kwargs={"k": 5})
            st.session_state.retriever = retriever  # Store retriever for keyword search

            # Step 6: Create RAG chain
            status_text.text("🤖 Setting up AI assistant...")
            progress_bar.progress(95)

            st.session_state.rag_chain = create_rag_chain(retriever)

            # Update cache with new repository data
            update_repo_cache(repo_url, REPO_DIR, DB_DIR, len(code_files), len(documents), language_stats)

            # Log successful indexing
            indexing_stats = {
                'file_count': len(code_files),
                'chunk_count': len(documents),
                'languages': language_stats
            }
            log_repo_indexing_complete(repo_url, indexing_stats)

            # Success!
            progress_bar.progress(100)
            status_text.text("✅ Repository indexed successfully!")
            details_text.empty()

            # Display summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Files Processed", len(code_files))
            with col2:
                st.metric("Code Chunks", len(documents))
            with col3:
                st.metric("Languages", len(language_stats))

            st.info("🎉 You can now ask questions about the codebase!")

        except Exception as e:
            log_error(e, "repository_indexing")
            st.error(f"❌ An error occurred: {e}")
            progress_bar.empty()
            status_text.empty()
            details_text.empty()

# --- Q&A Section ---
st.subheader("Ask a Question")

if st.session_state.rag_chain is None:
    st.info("Please index a repository first.")
else:
    # Search mode selection
    search_mode = st.radio(
        "Search Mode:",
        ["🔍 Semantic Search (AI-powered)", "📝 Keyword Search (exact matches)"],
        horizontal=True,
        help="Semantic search understands meaning, keyword search finds exact text matches"
    )

    user_question = st.text_input("Your question:", placeholder="e.g., How is the application context managed in Flask?")

    col1, col2 = st.columns([4, 1])
    with col1:
        ask_button = st.button("🤔 Ask Question", type="primary")
    with col2:
        if st.button("🔄 Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()

    def keyword_search(question, top_k=5):
        """Direct keyword-based search through all documents."""
        keywords = question.lower().split()
        scored_docs = []

        try:
            # Get all documents from the vector store directly
            # This gives us access to all chunks, not just semantically similar ones
            all_docs = []

            # Get documents from vector store for keyword search
            if st.session_state.retriever and hasattr(st.session_state.retriever, 'vectorstore'):
                try:
                    vectorstore = st.session_state.retriever.vectorstore

                    # Method 1: Try to access ChromaDB collection directly
                    if hasattr(vectorstore, '_collection'):
                        try:
                            collection = vectorstore._collection
                            results = collection.get(include=['documents', 'metadatas'])

                            if results and results['documents']:
                                from langchain.docstore.document import Document
                                all_docs = []
                                for i, doc_content in enumerate(results['documents']):
                                    metadata = results['metadatas'][i] if i < len(results['metadatas']) else {}
                                    doc = Document(page_content=doc_content, metadata=metadata)
                                    all_docs.append(doc)
                            else:
                                all_docs = []
                        except Exception as e:
                            print(f"Direct collection access failed: {e}")
                            all_docs = []
                    else:
                        all_docs = []

                    # Method 2: Fallback - use broad semantic searches to get diverse documents
                    if not all_docs or len(all_docs) < 10:
                        print("Using fallback method for document retrieval...")
                        search_terms = ["function", "class", "import", "def", "const", "let", "var", "export", "return"]
                        seen_contents = set()
                        fallback_docs = []

                        for term in search_terms[:3]:  # Limit to first 3 terms for speed
                            try:
                                docs = vectorstore.similarity_search(term, k=30)
                                for doc in docs:
                                    if doc.page_content not in seen_contents:
                                        fallback_docs.append(doc)
                                        seen_contents.add(doc.page_content)
                                        if len(fallback_docs) >= 100:  # Reasonable limit
                                            break
                            except Exception as e:
                                print(f"Search failed for term '{term}': {e}")
                                continue

                        if fallback_docs:
                            all_docs.extend(fallback_docs)
                        elif not all_docs:
                            return "Unable to retrieve documents from vector store. Please try re-indexing the repository."

                    if not all_docs:
                        return "No documents found in the codebase. Please index a repository first."

                except Exception as e:
                    return f"Error accessing vector store: {str(e)}"
            else:
                return "Retriever not available for keyword search. Please index a repository first."

            if not all_docs:
                return "No documents found in the codebase. Please index a repository first."

            # Score each document based on keyword matches
            for doc in all_docs:
                content = doc.page_content.lower()
                score = 0

                # Count keyword matches (with position weighting)
                for i, keyword in enumerate(keywords):
                    if keyword in content:
                        # Give higher weight to matches earlier in the question
                        score += (len(keywords) - i) * content.count(keyword)

                if score > 0:
                    scored_docs.append((doc, score))

            # Sort by score and take top results
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            top_results = scored_docs[:top_k]

            if top_results:
                answer_parts = []
                for i, (doc, score) in enumerate(top_results):
                    source_file = doc.metadata.get('source', 'unknown')
                    # Find the context around the first keyword match
                    content = doc.page_content
                    content_lower = content.lower()

                    # Find first keyword in content
                    keyword_positions = []
                    for keyword in keywords:
                        pos = content_lower.find(keyword)
                        if pos != -1:
                            keyword_positions.append(pos)

                    if keyword_positions:
                        start_pos = max(0, min(keyword_positions) - 50)
                        end_pos = min(len(content), min(keyword_positions) + 200)
                        preview = content[start_pos:end_pos]
                        if start_pos > 0:
                            preview = "..." + preview
                        if end_pos < len(content):
                            preview = preview + "..."
                    else:
                        preview = content[:200] + "..." if len(content) > 200 else content

                    answer_parts.append(f"**Match {i+1}** (score: {score})\n**File:** {source_file}\n{preview}")

                answer = "\n\n" + "\n\n".join(answer_parts)
                return f"Found {len(top_results)} keyword matches:\n{answer}"
            else:
                return f"No matches found for keywords: {', '.join(keywords)}. Try using semantic search for more flexible matching or different keywords."

        except Exception as e:
            return f"Error during keyword search: {str(e)}"

    if ask_button and user_question:
        start_time = datetime.now()

        if "Semantic Search" in search_mode:
            spinner_text = "🧠 Analyzing codebase with AI..."
        else:
            spinner_text = "🔍 Searching for exact keyword matches..."

        with st.spinner(spinner_text):
            try:
                if "Semantic Search" in search_mode:
                    # Use RAG pipeline for semantic search
                    answer = st.session_state.rag_chain.invoke(user_question)
                else:
                    # Use keyword search
                    answer = keyword_search(user_question)

                processing_time = (datetime.now() - start_time).total_seconds()

                # Log query with search mode
                from logger import log_performance
                log_performance("query_processing", processing_time, {"mode": search_mode, "question_length": len(user_question)})

                # Store in chat history
                if 'chat_history' not in st.session_state:
                    st.session_state.chat_history = []

                st.session_state.chat_history.append({
                    'question': user_question,
                    'answer': answer,
                    'timestamp': datetime.now().isoformat(),
                    'processing_time': processing_time,
                    'search_mode': search_mode
                })

                st.markdown("### 💡 Answer")
                st.markdown(answer)

                # Show confidence indicator (basic)
                if len(answer) > 100:
                    st.success("✅ High confidence answer (detailed response)")
                elif len(answer) > 50:
                    st.info("ℹ️ Moderate confidence answer")
                else:
                    st.warning("⚠️ Limited information available")

                # Show processing time and mode
                st.caption(f"⚡ Processed in {processing_time:.2f} seconds using {search_mode}")

            except Exception as e:
                log_error(e, "query_processing")
                st.error(f"❌ Error processing question: {e}")

    # Display chat history
    if 'chat_history' in st.session_state and st.session_state.chat_history:
        st.subheader("💬 Conversation History")
        for i, chat in enumerate(reversed(st.session_state.chat_history[-5:])):  # Show last 5
            search_mode_indicator = "🔍" if "Semantic" in chat.get('search_mode', '') else "📝"
            with st.expander(f"{search_mode_indicator} {chat['question'][:50]}...", expanded=(i==0)):
                st.markdown(f"**Question:** {chat['question']}")
                st.markdown(f"**Answer:** {chat['answer']}")
                st.caption(f"Asked at: {chat['timestamp'][:19]} | Mode: {chat.get('search_mode', 'Unknown')} | ⏱️ {chat.get('processing_time', 0):.2f}s")

# --- Sidebar with Export Options ---
create_export_ui()