# rag_chain.py
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

def create_rag_chain(retriever):
    """
    Creates the RAG (Retrieval-Augmented Generation) chain.
    """
    # Define the prompt template
    # This template is crucial. It guides the LLM on how to use the retrieved code context.
    template = """
    You are an expert programmer and a helpful AI assistant for understanding codebases.
    Answer the user's question based ONLY on the following context of code snippets.
    If the context does not contain the answer, state that you don't have enough information.
    Do not make up answers.

    Context:
    {context}

    Question:
    {question}

    Answer:
    """
    prompt = ChatPromptTemplate.from_template(template)

    # Initialize the LLM - Using Google Gemini (FREE!)
    from langchain_google_genai import ChatGoogleGenerativeAI

    model_name = os.getenv("LLM_MODEL", "gemini-1.5-flash")  # Use Gemini 1.5 Flash (free)
    temperature = float(os.getenv("TEMPERATURE", "0.1"))

    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    # Create the RAG chain using LangChain Expression Language (LCEL)
    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain