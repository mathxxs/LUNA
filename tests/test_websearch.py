import pytest
from unittest.mock import patch, MagicMock
from core.websearch import search_and_fetch

@pytest.mark.parametrize("url,expected", [
    ("https://italiancoders.it/t/deploy/", True),
    ("https://example.com/tag/python", True),
    ("https://blog.altervista.org/cose", True),
    ("https://example.blogspot.com/post", True),
    ("https://example.com/?q=ricerca", True),
    ("https://towardsdatascience.com/intro-to-random-forest", False),
    ("https://scikit-learn.org/stable/modules/clustering.html", False),
    ("https://it.wikipedia.org/wiki/Random_forest", False),
    ("https://medium.com/@autore/titolo-articolo", False),
])
def test_is_low_quality_url(url, expected):
    from core.websearch import _is_low_quality_url
    assert _is_low_quality_url(url) is expected

def test_search_and_fetch_schema_offline():
    """Mocked DDGS + extract returns dicts with the expected schema."""
    fake_hit = {
        "href": "https://example.com",
        "title": "Esempio",
        "body": "Snippet di prova",
    }
    with patch("core.websearch.DDGS") as MockDDGS, \
         patch("core.websearch.extract_text_from_url", return_value="contenuto del corpo"):
        instance = MagicMock()
        instance.text.return_value = [fake_hit]
        MockDDGS.return_value.__enter__.return_value = instance

        results = search_and_fetch("test query", k=1)

    assert len(results) == 1
    r = results[0]
    assert r["title"] == "Esempio"
    assert r["url"] == "https://example.com"
    assert r["snippet"] == "Snippet di prova"
    assert r["fulltext"] == "contenuto del corpo"

@pytest.mark.slow
def test_search_and_fetch_live():
    """Live DDGS — at least one hit with non-empty url."""
    results = search_and_fetch("python language", k=3)
    assert len(results) >= 1
    assert results[0]["url"].startswith("http")
