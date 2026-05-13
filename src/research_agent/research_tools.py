import xml.etree.ElementTree

import httpx
import langchain_core.tools


@langchain_core.tools.tool
async def search_semantic_scholar(query: str, limit: int = 5) -> list[dict]:
    """
    Search Semantic Scholar for recent academic papers related to a query.
    Returns paper titles, abstracts, years, URLs, and citation counts.
    """
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": limit,
        "fields": "title,abstract,year,url,citationCount,authors",
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()

    data = response.json()
    results = []

    for paper in data.get("data", []):
        results.append(
            {
                "source": "semantic_scholar",
                "title": paper.get("title"),
                "abstract": paper.get("abstract"),
                "year": paper.get("year"),
                "url": paper.get("url"),
                "citation_count": paper.get("citationCount"),
                "authors": [author.get("name") for author in paper.get("authors", [])],
            }
        )

    return results


@langchain_core.tools.tool
async def search_arxiv(query: str, max_results: int = 5) -> list[dict]:
    """
    Search arXiv for recent papers related to a query.
    Returns title, summary, authors, publication date, and URL.
    """
    url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()

    root = xml.etree.ElementTree.fromstring(response.text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    results = []

    for entry in root.findall("atom:entry", ns):
        title = entry.find("atom:title", ns)
        summary = entry.find("atom:summary", ns)
        published = entry.find("atom:published", ns)
        link = entry.find("atom:id", ns)

        authors = [
            author.find("atom:name", ns).text  # type: ignore
            for author in entry.findall("atom:author", ns)
            if author.find("atom:name", ns) is not None
        ]

        results.append(
            {
                "source": "arxiv",
                "title": title.text.strip() if title is not None else None,
                "summary": summary.text.strip() if summary is not None else None,
                "published": published.text if published is not None else None,
                "url": link.text if link is not None else None,
                "authors": authors,
            }
        )

    return results
