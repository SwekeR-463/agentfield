"""Research execution router with Tavily integration."""

from __future__ import annotations

import os
from typing import List

from agentfield import AgentRouter

from schemas import Citation, ResearchFindings, SearchQueries, TaskResult


research_router = AgentRouter(prefix="research")


@research_router.reasoner()
async def generate_search_queries(
    task_description: str, research_question: str
) -> SearchQueries:
    """Generate focused search queries for a research task."""
    response = await research_router.ai(
        system=(
            "You are a search query expert. Generate 2-4 focused search queries "
            "optimized for web search that will help answer the research task.\n\n"
            "Each query should be:\n"
            "- Specific and targeted\n"
            "- Use relevant keywords\n"
            "- Different angles/aspects of the task\n\n"
            "Return ONLY a JSON object with a 'queries' array of search strings."
        ),
        user=(
            f"Research Question: {research_question}\n"
            f"Task: {task_description}\n\n"
            f"Generate 2-4 search queries to research this task."
        ),
        schema=SearchQueries,
    )
    return response


@research_router.reasoner()
async def execute_search(queries: List[str]) -> dict:
    """Execute Tavily search for given queries."""
    try:
        from tavily import TavilyClient
    except ImportError:
        raise ImportError("tavily-python not installed. Run: pip install tavily-python")

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY environment variable not set")

    client = TavilyClient(api_key=api_key)

    # Execute searches in parallel
    all_results = []
    for query in queries:
        try:
            result = client.search(
                query=query,
                search_depth="advanced",
                max_results=5,
                include_answer=False,
                include_raw_content=True,
            )
            all_results.append(result)
        except Exception as e:
            # Continue with other queries if one fails
            all_results.append({"error": str(e), "query": query})

    # Combine results
    combined = {
        "results": [],
        "queries": queries,
    }

    for result in all_results:
        if "error" not in result and "results" in result:
            combined["results"].extend(result["results"])

    return combined


@research_router.reasoner()
async def synthesize_findings(
    task_description: str,
    research_question: str,
    search_results: dict,
) -> ResearchFindings:
    """Synthesize search results into structured findings with citations."""
    # Format search results for the prompt
    results_text = ""
    citations_data = []

    for idx, result in enumerate(search_results.get("results", [])[:10]):
        title = result.get("title", "Untitled")
        url = result.get("url", "")
        content = result.get("content", "")
        raw_content = result.get("raw_content", "")

        excerpt = raw_content[:500] if raw_content else content[:300]
        results_text += f"\n[{idx+1}] {title}\nURL: {url}\nContent: {excerpt}\n"

        citations_data.append({"url": url, "title": title, "excerpt": excerpt})

    response = await research_router.ai(
        system=(
            "You are a research synthesis expert. Synthesize search results into "
            "structured findings with numbered points.\n\n"
            "Format findings as:\n"
            "1. First finding [1] (reference by number)\n"
            "2. Second finding [2]\n"
            "etc.\n\n"
            "Extract citations: for each numbered reference, provide URL, title, and excerpt.\n\n"
            "Assess confidence: 'high' if comprehensive, 'medium' if partial, 'low' if insufficient."
        ),
        user=(
            f"Research Question: {research_question}\n"
            f"Task: {task_description}\n\n"
            f"Search Results:{results_text}\n\n"
            f"Synthesize findings with numbered points and citations. "
            f"Reference sources by number [1], [2], etc."
        ),
        schema=ResearchFindings,
    )

    # Map citations from search results
    citation_map = {idx + 1: Citation(**c) for idx, c in enumerate(citations_data)}

    # Update citations in response based on references in findings
    final_citations = []
    for i in range(1, len(citations_data) + 1):
        if f"[{i}]" in response.findings and i in citation_map:
            final_citations.append(citation_map[i])

    response.citations = final_citations
    return response


@research_router.reasoner()
async def execute_research_task(
    task_id: str,
    task_description: str,
    research_question: str,
) -> TaskResult:
    """Orchestrate research execution: queries → search → synthesize."""
    # Generate search queries
    queries_response = await generate_search_queries(
        task_description, research_question
    )

    # Execute search
    search_results = await execute_search(queries_response.queries)

    # Synthesize findings
    findings_response = await synthesize_findings(
        task_description, research_question, search_results
    )

    # Convert to TaskResult
    sources = [f"{c.title} ({c.url})" for c in findings_response.citations]

    return TaskResult(
        task_id=task_id,
        description=task_description,
        findings=findings_response.findings,
        sources=sources,
        confidence=findings_response.confidence,
    )
