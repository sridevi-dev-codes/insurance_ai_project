import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

from app.core.db import get_vector_store

load_dotenv()

_raw_conn = os.getenv("PG_CONNECTION_STRING", "").replace(
 "postgresql+psycopg", "postgresql")

def query_documents(query: str, k: int = 5) -> list[dict]:
    """
    Semantic search using vector DB.
    """
    vector_store = get_vector_store()
    docs = vector_store.similarity_search(query, k=k)
    return [
        {
            "content": d.page_content,
            "metadata": d.metadata
        }
        for d in docs
    ]

def fts_search(query: str, k: int = 5, collection_name: str = "insurance_docs") -> list[dict]:
    """
    PostgreSQL full-text search for insurance clauses.
    """
    sql = """
        SELECT
            e.document AS content,
            e.cmetadata AS metadata,
            ts_rank(
                to_tsvector('english', e.document),
                plainto_tsquery('english', %(query)s)
            ) AS fts_rank
        FROM langchain_pg_embedding e
        JOIN langchain_pg_collection c ON c.uuid = e.collection_id
        WHERE c.name = %(collection)s
          AND to_tsvector('english', e.document)
              @@ plainto_tsquery('english', %(query)s)
        ORDER BY fts_rank DESC
        LIMIT %(k)s;
    """
    with psycopg.connect(_raw_conn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, {
                "query": query,
                "collection": collection_name,
                "k": k
            })
            rows = cur.fetchall()
    return [
        {
            "content": r["content"],
            "metadata": r["metadata"],
            "fts_rank": float(r["fts_rank"]),
        }
        for r in rows
    ]

def hybrid_search(query: str, k: int = 5) -> list[dict]:
    """
    Combines vector + FTS using Reciprocal Rank Fusion (RRF).
    """
    vector_store = get_vector_store()
    vector_docs = vector_store.similarity_search(query, k=k)
    fts_docs = fts_search(query, k=k)
    rrf_scores: dict[str, float] = {}
    chunk_map: dict[str, dict] = {}
    for rank, doc in enumerate(vector_docs):
        key = doc.page_content[:120]   
        rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (60 + rank + 1)
        chunk_map[key] = {
            "content": doc.page_content,
            "metadata": doc.metadata
        }
    for rank, doc in enumerate(fts_docs):
        key = doc["content"][:120]    
        rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (60 + rank + 1)
        chunk_map[key] = {
            "content": doc["content"],
            "metadata": doc["metadata"]
        }

    ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return [chunk_map[key] for key, _ in ranked[:k]]