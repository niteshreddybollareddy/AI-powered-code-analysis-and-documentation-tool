# vector_store.py
import os
import chromadb
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

# Read embedding model from environment variables
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

def create_vector_store(documents, persist_directory="./chroma_db"):
    """
    Creates a ChromaDB vector store from a list of documents.
    """
    print("Creating embedding function...")
    embedding_function = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    
    print(f"Creating vector store in '{persist_directory}'...")
    db = Chroma.from_documents(
        documents, 
        embedding_function,
        persist_directory=persist_directory
    )
    print("Vector store created successfully.")
    return db

def load_vector_store(persist_directory="./chroma_db"):
    """
    Loads an existing ChromaDB vector store.
    """
    print("Loading vector store...")
    embedding_function = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    db = Chroma(persist_directory=persist_directory, embedding_function=embedding_function)
    print("Vector store loaded.")
    return db