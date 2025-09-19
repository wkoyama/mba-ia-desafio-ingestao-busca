import os
from dotenv import load_dotenv
from typing import List, Tuple

load_dotenv()

from langchain_postgres import PGVector
from langchain_google_genai import GoogleGenerativeAIEmbeddings

try:
    from langchain_google_genai import GoogleGenerativeAI
except Exception:
    GoogleGenerativeAI = None

PGHOST = os.environ.get("PGHOST", "localhost")
PGPORT = int(os.environ.get("PGPORT", 5432))
PGUSER = os.environ.get("PGUSER", "postgres")
PGPASSWORD = os.environ.get("PGPASSWORD", "postgres")
PGDATABASE = os.environ.get("PGDATABASE", "langchain_db")
TABLE_NAME = os.environ.get("TABLE_NAME", "documents")
TOP_K = int(os.environ.get("TOP_K", 10))


def get_embedding_client():
    if GoogleGenerativeAIEmbeddings is None:
        raise RuntimeError("GoogleGenerativeAIEmbeddings não disponível.")
    return GoogleGenerativeAIEmbeddings(api_key=os.environ.get("GOOGLE_API_KEY"), model="models/embedding-001")

def get_vector_store():
    if PGVector is None:
        raise RuntimeError("langchain_postgres.PGVector não disponível — instale a dependência certa.")
    
    # Criar string de conexão
    connection_string = f"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}"
    
    embeddings = get_embedding_client()
    vectordb = PGVector(
        connection=connection_string,
        collection_name=TABLE_NAME,
        embeddings=embeddings,
        use_jsonb=True
    )
    return vectordb

def semantic_search_with_score(query: str, k: int = TOP_K) -> List[Tuple[str, float, dict]]:
    """
    Retorna lista de tuplas (texto, score, metadata)
    """
    vectordb = get_vector_store()
    # alguns wrappers oferecem similarity_search_with_score(query, k)
    if hasattr(vectordb, "similarity_search_with_score"):
        results = vectordb.similarity_search_with_score(query, k=k)
        # results geralmente é lista de (Document, score)
        formatted = []
        for item, score in results:
            text = getattr(item, "page_content", item.get("text") if isinstance(item, dict) else str(item))
            meta = getattr(item, "metadata", item.get("metadata", {})) if isinstance(item, (dict,)) else getattr(item, "metadata", {})
            formatted.append((text, score, meta))
        return formatted
    else:
        # Tentar método search
        if hasattr(vectordb, "search"):
            results = vectordb.search(query, top_k=k)
            return [(r["text"], r.get("score", 0.0), r.get("metadata", {})) for r in results]
        raise RuntimeError("O vetor DB não tem método similarity_search_with_score nem search. Verifique a versão do langchain_postgres.")

PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""

def get_llm():    
    if GoogleGenerativeAI is None:
        raise RuntimeError("GoogleGenerativeAI não disponível — instale langchain-google-genai.")
    google_key = os.environ.get("GOOGLE_API_KEY")
    if not google_key:
        raise RuntimeError("Defina GOOGLE_API_KEY no .env")
    return GoogleGenerativeAI(api_key=google_key, model="gemini-2.5-flash-lite", temperature=0.0, max_tokens=512)

def build_context(results: List[tuple]) -> str:
    """
    results: lista de (texto, score, metadata)
    Concatenar os textos em ordem com separadores e referências se houver.
    """
    parts = []
    for i, (text, score, meta) in enumerate(results):
        ref = meta.get("source", f"chunk_{meta.get('chunk_id','?')}")
        parts.append(f"--- Documento {i+1} | score={score:.4f} | source={ref}\n{text}")
    return "\n\n".join(parts)

def search_prompt(question=None):
    # obter top k resultados
    results = semantic_search_with_score(question, k=TOP_K)
    context = build_context(results)

    prompt = PROMPT_TEMPLATE.format(contexto=context, pergunta=question)

    llm = get_llm()
    # usar invoke em vez de predict (método recomendado)
    answer = None
    if hasattr(llm, "invoke"):
        answer = llm.invoke(prompt)
    elif hasattr(llm, "predict"):
        answer = llm.predict(prompt)
    else:
        # fallback: tentar __call__
        try:
            answer = llm(prompt)
        except Exception as e:
            raise RuntimeError("Não foi possível chamar o LLM com a interface atual: " + str(e))

    # limpeza: às vezes o LLM agrega citações; retornar o conteúdo limpo
    print("\nRESPOSTA:")
    print(answer.strip())
    return answer.strip()