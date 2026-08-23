import os
from langchain_community.document_loaders import TextLoader, PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

DATA_PATH = "data"
DB_PATH = "faiss_db"

def create_vector_db():
    print("Loading documents from 'data' directory...")
    # Load text files
    loader_txt = DirectoryLoader(DATA_PATH, glob="*.txt", loader_cls=TextLoader)
    documents = loader_txt.load()
    
    # Load pdf files
    try:
        loader_pdf = DirectoryLoader(DATA_PATH, glob="*.pdf", loader_cls=PyPDFLoader)
        documents.extend(loader_pdf.load())
    except Exception as e:
        print(f"Could not load PDFs, PyPDFLoader error: {e}")
    
    print(f"Loaded {len(documents)} documents.")
    if not documents:
        print("No documents found. Please add .txt or .pdf files to the 'data' folder.")
        return

    print("Chunking texts...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    texts = text_splitter.split_documents(documents)
    print(f"Split into {len(texts)} chunks.")
    
    print("Creating embeddings (downloading model if first run)...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    print("Building FAISS database...")
    db = FAISS.from_documents(texts, embeddings)
    db.save_local(DB_PATH)
    print(f"Database successfully saved to {DB_PATH}")

if __name__ == "__main__":
    os.makedirs(DATA_PATH, exist_ok=True)
    create_vector_db()
