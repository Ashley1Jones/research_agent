import xml.etree.ElementTree
import typing
import logging
import httpx

import langchain_core.tools

import research_agent.states

HttpxQueryParamValue = str | int | float | bool | None | typing.Sequence[str | int | float | bool | None]


async def run_literature_tool(
    tool: typing.Any,
    query: str,
    args: dict[str, typing.Any],
) -> list[research_agent.states.LiteratureResult]:
    try:
        results = await tool.ainvoke(args)
    except Exception as exc:
        logging.warning("Literature tool failed for args %s: %s", args, exc)
        return []

    literature_results = []
    for result in typing.cast(list[dict[str, typing.Any]], results):
        result_with_query = {**result, "query": query}
        literature_results.append(typing.cast(research_agent.states.LiteratureResult, result_with_query))

    return literature_results


@langchain_core.tools.tool
async def search_semantic_scholar(query: str, limit: int = 5) -> list[dict[str, typing.Any]]:
    """
    Search Semantic Scholar for recent academic papers related to a query.
    Returns paper titles, abstracts, years, URLs, and citation counts.
    """
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params: dict[str, HttpxQueryParamValue] = {
        "query": query,
        "limit": limit,
        "fields": "title,abstract,year,url,citationCount,authors",
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()

    data = typing.cast(dict[str, typing.Any], response.json())
    results: list[dict[str, typing.Any]] = []

    for paper in data.get("data", []):
        paper_data = typing.cast(dict[str, typing.Any], paper)
        authors = typing.cast(list[dict[str, typing.Any]], paper_data.get("authors", []))
        results.append(
            {
                "source": "semantic_scholar",
                "title": paper_data.get("title"),
                "abstract": paper_data.get("abstract"),
                "year": paper_data.get("year"),
                "url": paper_data.get("url"),
                "citation_count": paper_data.get("citationCount"),
                "authors": [author.get("name") for author in authors],
            }
        )

    return results


@langchain_core.tools.tool
async def search_arxiv(query: str, max_results: int = 5) -> list[dict[str, typing.Any]]:
    """
    Search arXiv for recent papers related to a query.
    Returns title, summary, authors, publication date, and URL.
    """
    url = "https://export.arxiv.org/api/query"
    params: dict[str, HttpxQueryParamValue] = {
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
    results: list[dict[str, typing.Any]] = []

    for entry in root.findall("atom:entry", ns):
        title = entry.find("atom:title", ns)
        summary = entry.find("atom:summary", ns)
        published = entry.find("atom:published", ns)
        link = entry.find("atom:id", ns)

        authors = []
        for author in entry.findall("atom:author", ns):
            author_name = text_or_none(author.find("atom:name", ns))
            if author_name is not None:
                authors.append(author_name)

        results.append(
            {
                "source": "arxiv",
                "title": text_or_none(title),
                "summary": text_or_none(summary),
                "published": text_or_none(published),
                "url": text_or_none(link),
                "authors": authors,
            }
        )

    return results


def text_or_none(element: xml.etree.ElementTree.Element | None) -> str | None:
    if element is None or element.text is None:
        return None

    return element.text.strip()
