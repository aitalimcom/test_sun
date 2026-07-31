"""
Build Vector Store — Index knowledge base documents for RAG
Run: python scripts/build_vectorstore.py
"""

from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).parent.parent / "database" / "knowledge"


def build():
    """Build ChromaDB vector store from knowledge base markdown files."""
    print("📚 Building vector store from knowledge base...\n")

    # Count documents
    md_files = list(KNOWLEDGE_DIR.rglob("*.md"))
    print(f"Found {len(md_files)} documents:")
    for f in md_files:
        print(f"  • {f.relative_to(KNOWLEDGE_DIR)}")

    # TODO: Uncomment when dependencies are installed
    # from langchain_community.document_loaders import DirectoryLoader
    # from langchain.text_splitter import RecursiveCharacterTextSplitter
    # from langchain_community.vectorstores import Chroma
    # from langchain_community.embeddings import HuggingFaceEmbeddings
    #
    # loader = DirectoryLoader(str(KNOWLEDGE_DIR), glob="**/*.md")
    # docs = loader.load()
    # print(f"\nLoaded {len(docs)} documents")
    #
    # splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    # chunks = splitter.split_documents(docs)
    # print(f"Split into {len(chunks)} chunks")
    #
    # embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    # vectorstore = Chroma.from_documents(
    #     chunks, embeddings,
    #     persist_directory=str(Path(__file__).parent.parent / "backend" / ".vectorstore")
    # )
    # print(f"\n✅ Vector store built with {len(chunks)} chunks")

    print("\n⏳ Vector store building requires: pip install chromadb sentence-transformers")
    print("   Run after installing dependencies.")


if __name__ == "__main__":
    build()
