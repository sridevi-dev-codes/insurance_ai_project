from langchain.tools import tool
from app.retrieval.search import query_documents,fts_search,hybrid_search

@tool
def vector_search_tool(query: str) -> str:
    """
    Use for:
    - insurance coverage interpretation
    - eligibility reasoning
    - semantic policy understanding
    """
    print("***TOOL USED: VECTOR SEARCH")
    print("Query:", query)
    results = query_documents(query, k=5)
    return format_results(results)

@tool
def keyword_search_tool(query: str) -> str:
    """
    Use for:
    - policy IDs
    - clause numbers
    - legal references
    """
    print("***TOOL USED: keyword SEARCH")
    print("Query:", query)
    results = fts_search(query, k=5)
    return format_results(results)


@tool
def hybrid_search_tool(query: str) -> str:
    """
    Use when both:
    - semantic meaning
    - exact keyword matching
    are needed.
    """
    print("***TOOL USED: hybrid SEARCH")
    print("Query:", query)
    results = hybrid_search(query, k=5)
    # print("TOOL O/P:", )
    return format_results(results)

def format_results(results: list[dict]) -> str:
    """
    Return LLM-safe string BUT preserves structured citation info
    """

    if not results:
        return "No relevant insurance documents found."

    formatted_chunks = []

    for r in results:
        content = r.get("content", "").strip()
        meta = r.get("metadata", {}) or {}

        page = meta.get("page", "N/A")
        qno = meta.get("question_no") or meta.get("q_no") or ""

        # Build strong citation line
        if qno:
            formatted_chunks.append(f"(Page {page}) Q{qno}: {content}")
        else:
            formatted_chunks.append(f"(Page {page}) {content}")
    # print('TOOL O?P:',formatted_chunks)
    return "\n\n".join(formatted_chunks)

# def format_results(results: list[dict]) -> dict:
#     """
#     Returns structured retrieval output for citations + documents
#     Includes page numbers in citations.
#     """

#     if not results:
#         return {
#             "text": "",
#             "citations": [],
#             "retrieved_documents": []
#         }

#     citations = []
#     retrieved_documents = set()
#     formatted_chunks = []

#     for r in results:
#         content = r.get("content", "").strip()
#         meta = r.get("metadata", {}) or {}

#         # Document source / filenam
#         source = meta.get("source") or meta.get("file_name") or "unknown_document"
#         retrieved_documents.add(source)

#         # Page number (if exists)
#         page = meta.get("page", "N/A")

#         # Citation format with page number
#         citations.append(f"(Page {page}) {content}")

#         formatted_chunks.append(content)
#     data = {
#     "text": "\n\n".join(formatted_chunks),
#     "citations": citations,
#     "retrieved_documents": list(retrieved_documents)
# }

#     print("TOOL O/P:",data)
#     return {
#         "text": "\n\n".join(formatted_chunks),
#         "citations": citations,
#         "retrieved_documents": list(retrieved_documents)
#     }

# def format_results(results: list[dict]) -> str:
#     """
#     Converts DB output into clean LLM context.
#     """

#     if not results:
#         return "No relevant insurance documents found."

#     formatted = []

#     for i, r in enumerate(results, 1):
#         meta = r.get("metadata", {})

#         formatted.append(f"""
# Document {i}:
# -------------------------
# {r.get('content', '')}

# Source: {meta.get('source', 'unknown')}
# Page: {meta.get('page', 'N/A')}
# -------------------------
# """)

#     return "\n".join(formatted)