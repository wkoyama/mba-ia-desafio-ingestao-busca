import os
from dotenv import load_dotenv
from pathlib import Path
from tqdm import tqdm
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres import PGVector
from langchain_core.documents import Document

try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
except Exception:
    GoogleGenerativeAIEmbeddings = None

load_dotenv()

# Garante que PDF_PATH seja um Path, com default para 'document.pdf' na raiz
PDF_PATH = Path(os.getenv("PDF_PATH") or "document.pdf")
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

EMBEDDINGS_PROVIDER = os.environ.get("EMBEDDINGS_PROVIDER", "gemini").lower()

PGHOST = os.environ.get("PGHOST", "localhost")
PGPORT = int(os.environ.get("PGPORT", 5432))
PGUSER = os.environ.get("PGUSER", "postgres")
PGPASSWORD = os.environ.get("PGPASSWORD", "postgres")
PGDATABASE = os.environ.get("PGDATABASE", "langchain_db")

# Nome da tabela onde os embeddings serão armazenados
TABLE_NAME = os.environ.get("TABLE_NAME", "documents")

def get_embeddings():
    if GoogleGenerativeAIEmbeddings is None:
            raise RuntimeError("GoogleGenerativeAIEmbeddings não disponível — instale langchain-google-genai.")
    google_key = os.environ.get("GOOGLE_API_KEY")
    if not google_key:
        raise RuntimeError("Defina GOOGLE_API_KEY no .env")
    return GoogleGenerativeAIEmbeddings(api_key=google_key, model="models/embedding-001")

def ingest_pdf():
    if not PDF_PATH.exists():
        print(f"Arquivo {PDF_PATH} não encontrado. Coloque o PDF na raiz do repositório com nome 'document.pdf'.")
        return
    
    loader = PyPDFLoader(str(PDF_PATH))
    print("Carregando PDF...")
    docs = loader.load()  # lista de Document (text + metadata)

    print(f"Total páginas carregadas: {len(docs)}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = []
    for doc in docs:
        splitted = splitter.split_documents([doc])
        # split_documents retorna lista; acumulamos
        chunks.extend(splitted)

    print(f"Total chunks gerados: {len(chunks)}")

    embeddings = get_embeddings()

    # Inicializar PGVector (langchain_postgres)
    pg_url = f"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}"
    print(f"Conectando ao Postgres em {pg_url} ...")
    vectordb = PGVector(
        connection=pg_url,
        collection_name=TABLE_NAME,
        embeddings=embeddings,
        use_jsonb=True
    )
    
    print(f"Preparando para inserir documentos na coleção {TABLE_NAME}...")
    
    docs_to_add = []
    for i, chunk in enumerate(chunks):
        metadata = chunk.metadata.copy() if getattr(chunk, "metadata", None) else {}
        metadata.update({
            "chunk_id": i,
            # se o loader preencheu page_number, mantenha, senão None
            "source": metadata.get("source", str(PDF_PATH)),
        })
        docs_to_add.append(Document(
            page_content=chunk.page_content,
            metadata=metadata
        ))

    print("Inserindo embeddings no banco (pode demorar dependendo do tamanho do PDF)...")
    try:
        vectordb.add_documents(docs_to_add)
        print("Ingestão completa.")
    except Exception as e:
        # fallback: tentar inserir usando from_documents
        print("Inserção via add_documents falhou. Tentando método alternativo...")
        try:
            if hasattr(PGVector, "from_documents"):
                PGVector.from_documents(
                    documents=docs_to_add, 
                    connection=pg_url, 
                    collection_name=TABLE_NAME, 
                    embeddings=embeddings,
                    use_jsonb=True
                )
                print("Ingestão completa via from_documents.")
            else:
                raise e
        except Exception as e2:
            print("Falha ao inserir embeddings:", e2)
            raise


if __name__ == "__main__":
    ingest_pdf()