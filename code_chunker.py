# code_chunker.py
import ast
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter, Language
from langchain.docstore.document import Document

# Language-specific configurations
LANGUAGE_CONFIGS = {
    'python': {
        'extensions': ['.py', '.pyx', '.pyi'],
        'chunker': 'ast',
        'chunk_size': 1500,
        'chunk_overlap': 150
    },
    'javascript': {
        'extensions': ['.js', '.jsx', '.ts', '.tsx', '.mjs'],
        'chunker': 'langchain',
        'language': Language.JS,
        'chunk_size': 1200,
        'chunk_overlap': 120
    },
    'java': {
        'extensions': ['.java'],
        'chunker': 'langchain',
        'language': Language.JAVA,
        'chunk_size': 1400,
        'chunk_overlap': 140
    },
    'cpp': {
        'extensions': ['.cpp', '.cc', '.cxx', '.c++', '.hpp', '.hxx', '.h++'],
        'chunker': 'langchain',
        'language': Language.CPP,
        'chunk_size': 1300,
        'chunk_overlap': 130
    },
    'go': {
        'extensions': ['.go'],
        'chunker': 'langchain',
        'language': Language.GO,
        'chunk_size': 1400,
        'chunk_overlap': 140
    },
    'rust': {
        'extensions': ['.rs'],
        'chunker': 'langchain',
        'language': Language.RUST,
        'chunk_size': 1400,
        'chunk_overlap': 140
    },
    'markdown': {
        'extensions': ['.md', '.markdown'],
        'chunker': 'text',
        'chunk_size': 1000,
        'chunk_overlap': 100
    },
    'json': {
        'extensions': ['.json', '.yaml', '.yml', '.toml'],
        'chunker': 'text',
        'chunk_size': 800,
        'chunk_overlap': 80
    },
    'html': {
        'extensions': ['.html', '.htm', '.xml'],
        'chunker': 'text',
        'chunk_size': 900,
        'chunk_overlap': 90
    }
}

def detect_language(file_path):
    """Detect programming language based on file extension."""
    import os
    _, ext = os.path.splitext(file_path.lower())

    for lang, config in LANGUAGE_CONFIGS.items():
        if ext in config['extensions']:
            return lang, config

    return 'text', {
        'extensions': ['.txt', '.log', '.ini', '.cfg'],
        'chunker': 'text',
        'chunk_size': 1000,
        'chunk_overlap': 100
    }

def parse_python_code(file_path):
    """
    Parses a Python file and extracts functions and classes using AST.
    Returns a list of code chunks (as strings).
    """
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    chunks = []
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                chunk = ast.get_source_segment(content, node)
                if chunk:
                    chunks.append(chunk)
    except Exception as e:
        # If AST parsing fails, fall back to text splitting
        print(f"Could not parse {file_path} with AST. Falling back to text splitting. Error: {e}")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)
        chunks = text_splitter.split_text(content)

    return chunks

def parse_code_with_langchain(file_path, language_config):
    """Parse code using LangChain's language-specific splitters."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    try:
        # Import available splitters - handle missing ones gracefully
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        # Try to import language-specific splitters, but don't fail if they're missing
        available_splitters = {}
        try:
            from langchain_community.text_splitter import PythonCodeTextSplitter
            available_splitters['python'] = PythonCodeTextSplitter
        except ImportError:
            pass

        language = language_config.get('language')
        chunk_size = language_config.get('chunk_size', 1000)
        chunk_overlap = language_config.get('chunk_overlap', 100)

        # For now, use generic recursive splitter for all languages
        # This is more reliable than trying to use potentially missing specialized splitters
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
            keep_separator=True,
            length_function=len
        )

        return splitter.split_text(content)

    except Exception as e:
        print(f"Error parsing {file_path} with LangChain: {e}")
        # Ultimate fallback
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        return text_splitter.split_text(content)

def chunk_code_files(file_paths, progress_callback=None):
    """
    Chunks a list of code files using language-specific parsing strategies.
    Returns a list of LangChain Document objects with enhanced metadata.
    """
    from langchain.docstore.document import Document
    import os

    all_docs = []
    total_files = len(file_paths)

    for i, file_path in enumerate(file_paths):
        if progress_callback:
            progress_callback(f"Processing file {i+1}/{total_files}: {os.path.basename(file_path)}")

        try:
            # Detect language and get appropriate config
            language, config = detect_language(file_path)
            chunks = []

            # Choose appropriate chunking strategy
            if config['chunker'] == 'ast' and language == 'python':
                chunks = parse_python_code(file_path)
            elif config['chunker'] == 'langchain':
                chunks = parse_code_with_langchain(file_path, config)
            else:
                # Default text splitting
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=config.get('chunk_size', 1000),
                    chunk_overlap=config.get('chunk_overlap', 100)
                )
                chunks = text_splitter.split_text(content)

            # Create documents with enhanced metadata
            for j, chunk in enumerate(chunks):
                metadata = {
                    "source": file_path,
                    "language": language,
                    "chunk_index": j,
                    "total_chunks": len(chunks),
                    "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                    "chunker_type": config['chunker']
                }
                doc = Document(page_content=chunk, metadata=metadata)
                all_docs.append(doc)

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            # Create a document with the error for visibility
            error_doc = Document(
                page_content=f"Error processing file: {e}",
                metadata={"source": file_path, "error": True}
            )
            all_docs.append(error_doc)

    return all_docs

if __name__ == '__main__':
    # Example usage: First run code_loader.py to get files
    from code_loader import clone_repository, get_code_files
    
    repo_url = 'https://github.com/pallets/flask' # A smaller, well-known repo
    local_repo_path = 'temp_repo_flask'
    clone_repository(repo_url, local_repo_path)
    files = get_code_files(local_repo_path, extensions=['.py']) # Only python files for this example
    
    documents = chunk_code_files(files)
    print(f"Created {len(documents)} document chunks.")
    # Print a sample chunk
    print("\n--- Sample Chunk ---")
    print(documents[50].page_content)
    print(f"Source: {documents[50].metadata['source']}")