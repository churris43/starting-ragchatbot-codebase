from vector_store import SearchResults


def make_search_results(documents, metadatas, error=None):
    """Factory: build a SearchResults from parallel lists."""
    return SearchResults(
        documents=documents,
        metadata=metadatas,
        distances=[0.1] * len(documents),
        error=error,
    )
