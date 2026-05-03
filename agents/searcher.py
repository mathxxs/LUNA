from agents import ResearchState
from core.websearch import search_and_fetch
from core.progress import emit

def searcher(state: ResearchState) -> ResearchState:
    emit("Searcher", "INFO", "Starting…")
    
    sub_queries = state.get("sub_queries", [])
    hits = []
    
    for query in sub_queries:
        emit("Searcher", "INFO", f"Executing query: '{query}'")
        try:
            results = search_and_fetch(query, k=5)
            for hit in results:
                fulltext = hit.get("fulltext", "")
                
                # Filter < 200 chars or SEO spam
                if len(fulltext) < 200:
                    emit("Searcher", "INFO", f"Skipping {hit.get('url')} (length < 200)")
                    continue
                if fulltext.count("http") > 20:
                    emit("Searcher", "INFO", f"Skipping {hit.get('url')} (likely SEO spam, too many links)")
                    continue
                    
                # Truncate to 2000 chars
                hit["fulltext"] = fulltext[:2000]
                
                # Add origin query
                hit["query"] = query
                hits.append(hit)
                
        except Exception as e:
            emit("Searcher", "WARNING", f"Search failed for query '{query}': {e}")
            
    state["hits"] = hits
    emit("Searcher", "INFO", "Done.")
    return state
