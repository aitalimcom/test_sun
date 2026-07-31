"""Web search service wrapper using DuckDuckGo search."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class WebSearchService:
    """Queries DuckDuckGo search for agricultural news, techniques, or real-time trends."""

    def __init__(self) -> None:
        pass

    async def search(self, query: str, max_results: int = 3) -> list[dict[str, Any]]:
        """Perform search using DuckDuckGo."""
        logger.info(f"Querying DuckDuckGo for: '{query}'")
        try:
            from duckduckgo_search import DDGS
            
            results = []
            with DDGS() as ddgs:
                ddgs_gen = ddgs.text(query, max_results=max_results)
                for r in ddgs_gen:
                    results.append({
                        "title": r.get("title", ""),
                        "link": r.get("href", ""),
                        "snippet": r.get("body", ""),
                    })
            return results
        except Exception as e:
            logger.warning(f"DuckDuckGo search package direct query failed: {e}. Trying LangChain wrapper.")
            try:
                from langchain_community.tools import DuckDuckGoSearchRun
                search_run = DuckDuckGoSearchRun()
                output = search_run.invoke(query)
                return [{
                    "title": "DuckDuckGo Search Results",
                    "link": "https://duckduckgo.com",
                    "snippet": output
                }]
            except Exception as e2:
                logger.error(f"DuckDuckGo search fallback also failed: {e2}")
                # Mock result for offline/demo
                return [
                    {
                        "title": "नेपाल कृषि अनुसन्धान परिषद् (NARC)",
                        "link": "http://narc.gov.np",
                        "snippet": "धान बालीमा लाग्ने रोग तथा कीरा नियन्त्रण सम्बन्धी आधुनिक प्रविधिहरूको विकास।"
                    },
                    {
                        "title": "कृषि ज्ञान केन्द्र कार्यालय",
                        "link": "http://moald.gov.np",
                        "snippet": "चालू आर्थिक वर्षमा कृषकहरूका लागि अनुदान कार्यक्रम र जैविक मल वितरण तालिका।"
                    }
                ]


# Singleton
web_search_service = WebSearchService()
