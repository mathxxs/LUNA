import httpx
import trafilatura
from ddgs import DDGS
from core.progress import emit

def extract_text_from_url(url: str, timeout: int = 10) -> str:
    """Fetch URL and extract main body text using trafilatura."""
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            text = trafilatura.extract(response.text, include_comments=False, include_tables=False)
            if text:
                return text
            return ""
    except Exception as e:
        emit("WebSearch", "WARNING", f"Failed to extract text from {url}: {str(e)}")
        return ""

def _is_low_quality_url(url: str) -> bool:
    """Return True for URLs unlikely to be substantive articles.

    Filters:
      - Forum tag/category pages: path segments /t/, /tag/,
        /category/, /categoria/, /label/, /topic/.
      - Low-authority community hosting: altervista.org,
        blogspot.*, wordpress.com.
      - Internal search-result pages: q=, s=, search=, query=
        as primary query parameter.

    Conservative: when in doubt, do NOT filter.
    """
    url_lower = url.lower()
    
    if any(s in url_lower for s in ["/t/", "/tag/", "/category/", "/categoria/", "/label/", "/topic/"]):
        return True
    
    if any(h in url_lower for h in ["altervista.org", "wordpress.com", "blogspot."]):
        return True
        
    if any(p in url_lower for p in ["?q=", "&q=", "?s=", "&s=", "?search=", "&search=", "?query=", "&query="]):
        return True
        
    return False

def search_and_fetch(query: str, k: int = 5) -> list[dict]:
    """
    Search DuckDuckGo and fetch the text of the top k results.
    Returns list of dicts: {"title": str, "url": str, "snippet": str, "fulltext": str}
    """
    emit("WebSearch", "INFO", f"Searching for: '{query}'")
    results = []
    try:
        with DDGS() as ddgs:
            # We use max_results=k to limit DDGS
            raw_results = list(ddgs.text(query, max_results=k))
            
            for item in raw_results:
                url = item.get("href")
                if not url:
                    continue
                    
                if _is_low_quality_url(url):
                    emit("WebSearch", "INFO", f"Filtered low-quality URL: {url}")
                    continue
                    
                title = item.get("title", "")
                snippet = item.get("body", "")
                
                emit("WebSearch", "INFO", f"Fetching content from: {url}")
                fulltext = extract_text_from_url(url)
                
                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "fulltext": fulltext
                })
    except Exception as e:
        emit("WebSearch", "ERROR", f"Search failed for '{query}': {str(e)}")
        
    return results
