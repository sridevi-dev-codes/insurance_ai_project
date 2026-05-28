from langchain.tools import tool
from app.retrieval_data.search import query_documents,fts_search,hybrid_search

@tool
def vector_search_tool(query: str) -> str:
    """
    Use for:
    - insurance coverage interpretation
    - eligibility reasoning
    - semantic policy understanding
    """
    print("🔵 TOOL USED: VECTOR SEARCH")
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
    print("🔵 TOOL USED: keyword SEARCH")
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
    print("🔵 TOOL USED: hybrid SEARCH")
    print("Query:", query)
    results = hybrid_search(query, k=5)
    return format_results(results)

def format_results(results: list[dict]) -> str:
    """
    Converts DB output into clean LLM context.
    """

    if not results:
        return "No relevant insurance documents found."

    formatted = []

    for i, r in enumerate(results, 1):
        meta = r.get("metadata", {})

        formatted.append(f"""
Document {i}:
-------------------------
{r.get('content', '')}

Source: {meta.get('source', 'unknown')}
Page: {meta.get('page', 'N/A')}
-------------------------
""")

    return "\n".join(formatted)