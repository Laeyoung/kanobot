"""Web tools: web_search and web_fetch."""

import html
import json
import os
import re
from typing import Any
from urllib.parse import urlparse

import httpx

from kanobot.agent.tools.base import Tool

# Shared constants
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_2) AppleWebKit/537.36"
MAX_REDIRECTS = 5  # Limit redirects to prevent DoS attacks


def _strip_tags(text: str) -> str:
    """Remove HTML tags and decode entities."""
    text = re.sub(r'<script[\s\S]*?</script>', '', text, flags=re.I)
    text = re.sub(r'<style[\s\S]*?</style>', '', text, flags=re.I)
    text = re.sub(r'<[^>]+>', '', text)
    return html.unescape(text).strip()


def _normalize(text: str) -> str:
    """Normalize whitespace."""
    text = re.sub(r'[ \t]+', ' ', text)
    return re.sub(r'\n{3,}', '\n\n', text).strip()


def _validate_url(url: str) -> tuple[bool, str]:
    """Validate URL: must be http(s) with valid domain."""
    try:
        p = urlparse(url)
        if p.scheme not in ('http', 'https'):
            return False, f"Only http/https allowed, got '{p.scheme or 'none'}'"
        if not p.netloc:
            return False, "Missing domain"
        return True, ""
    except Exception as e:
        return False, str(e)


class WebSearchTool(Tool):
    """Search the web using Brave Search API."""
    
    name = "web_search"
    description = "Search the web. Returns titles, URLs, and snippets."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "count": {"type": "integer", "description": "Results (1-10)", "minimum": 1, "maximum": 10}
        },
        "required": ["query"]
    }
    
    def __init__(self, api_key: str | None = None, max_results: int = 5):
        self.api_key = api_key or os.environ.get("BRAVE_API_KEY", "")
        self.max_results = max_results
    
    async def execute(self, query: str, count: int | None = None, **kwargs: Any) -> str:
        if not self.api_key:
            return "Error: BRAVE_API_KEY not configured"
        
        try:
            n = min(max(count or self.max_results, 1), 10)
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    params={"q": query, "count": n},
                    headers={"Accept": "application/json", "X-Subscription-Token": self.api_key},
                    timeout=10.0
                )
                r.raise_for_status()
            
            results = r.json().get("web", {}).get("results", [])
            if not results:
                return f"No results for: {query}"
            
            lines = [f"Results for: {query}\n"]
            for i, item in enumerate(results[:n], 1):
                lines.append(f"{i}. {item.get('title', '')}\n   {item.get('url', '')}")
                if desc := item.get("description"):
                    lines.append(f"   {desc}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error: {e}"


class NaverSearchTool(Tool):
    """Search Naver, optimized for Korean content."""

    name = "naver_search"
    description = (
        "Search Naver (Korean search engine). Best for Korean-language queries. "
        "Supports web, blog, news, and encyclopedia search types."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query (Korean recommended)"},
            "type": {
                "type": "string",
                "enum": ["web", "blog", "news", "encyc"],
                "description": "Search type: web (default), blog, news, or encyc (encyclopedia)",
            },
            "count": {
                "type": "integer",
                "description": "Number of results (1-10)",
                "minimum": 1,
                "maximum": 10,
            },
            "sort": {
                "type": "string",
                "enum": ["sim", "date"],
                "description": "Sort order: sim (relevance, default) or date (newest first)",
            },
        },
        "required": ["query"],
    }

    _ENDPOINTS = {
        "web": "https://openapi.naver.com/v1/search/webkr.json",
        "blog": "https://openapi.naver.com/v1/search/blog.json",
        "news": "https://openapi.naver.com/v1/search/news.json",
        "encyc": "https://openapi.naver.com/v1/search/encyc.json",
    }

    def __init__(self, client_id: str = "", client_secret: str = "", max_results: int = 5):
        self.client_id = client_id
        self.client_secret = client_secret
        self.max_results = max_results

    async def execute(
        self,
        query: str,
        type: str = "web",
        count: int | None = None,
        sort: str = "sim",
        **kwargs: Any,
    ) -> str:
        if not self.client_id or not self.client_secret:
            return "Error: Naver API credentials not configured (client_id / client_secret)"

        endpoint = self._ENDPOINTS.get(type)
        if not endpoint:
            return f"Error: Invalid search type '{type}'. Use: web, blog, news, encyc"

        n = min(max(count or self.max_results, 1), 10)

        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    endpoint,
                    params={"query": query, "display": n, "sort": sort},
                    headers={
                        "X-Naver-Client-Id": self.client_id,
                        "X-Naver-Client-Secret": self.client_secret,
                    },
                    timeout=10.0,
                )
                if r.status_code == 429:
                    return "Error: Naver API rate limit exceeded. Please try again later."
                r.raise_for_status()

            items = r.json().get("items", [])
            if not items:
                return f"No results for: {query}"

            lines = [f"Results for: {query}\n"]
            for i, item in enumerate(items[:n], 1):
                title = _strip_tags(item.get("title", ""))
                link = item.get("link", "")
                desc = _strip_tags(item.get("description", ""))
                lines.append(f"{i}. {title}\n   {link}")
                if desc:
                    lines.append(f"   {desc}")
            return "\n".join(lines)
        except httpx.HTTPStatusError as e:
            return f"Error: Naver API returned status {e.response.status_code}"
        except Exception as e:
            return f"Error: {e}"


class WebFetchTool(Tool):
    """Fetch and extract content from a URL using Readability."""
    
    name = "web_fetch"
    description = "Fetch URL and extract readable content (HTML → markdown/text)."
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to fetch"},
            "extractMode": {"type": "string", "enum": ["markdown", "text"], "default": "markdown"},
            "maxChars": {"type": "integer", "minimum": 100}
        },
        "required": ["url"]
    }
    
    def __init__(self, max_chars: int = 50000):
        self.max_chars = max_chars
    
    async def execute(self, url: str, extractMode: str = "markdown", maxChars: int | None = None, **kwargs: Any) -> str:
        from readability import Document

        max_chars = maxChars or self.max_chars

        # Validate URL before fetching
        is_valid, error_msg = _validate_url(url)
        if not is_valid:
            return json.dumps({"error": f"URL validation failed: {error_msg}", "url": url})

        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                max_redirects=MAX_REDIRECTS,
                timeout=30.0
            ) as client:
                r = await client.get(url, headers={"User-Agent": USER_AGENT})
                r.raise_for_status()
            
            ctype = r.headers.get("content-type", "")
            
            # JSON
            if "application/json" in ctype:
                text, extractor = json.dumps(r.json(), indent=2), "json"
            # HTML
            elif "text/html" in ctype or r.text[:256].lower().startswith(("<!doctype", "<html")):
                doc = Document(r.text)
                content = self._to_markdown(doc.summary()) if extractMode == "markdown" else _strip_tags(doc.summary())
                text = f"# {doc.title()}\n\n{content}" if doc.title() else content
                extractor = "readability"
            else:
                text, extractor = r.text, "raw"
            
            truncated = len(text) > max_chars
            if truncated:
                text = text[:max_chars]
            
            return json.dumps({"url": url, "finalUrl": str(r.url), "status": r.status_code,
                              "extractor": extractor, "truncated": truncated, "length": len(text), "text": text})
        except Exception as e:
            return json.dumps({"error": str(e), "url": url})
    
    def _to_markdown(self, html: str) -> str:
        """Convert HTML to markdown."""
        # Convert links, headings, lists before stripping tags
        text = re.sub(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>([\s\S]*?)</a>',
                      lambda m: f'[{_strip_tags(m[2])}]({m[1]})', html, flags=re.I)
        text = re.sub(r'<h([1-6])[^>]*>([\s\S]*?)</h\1>',
                      lambda m: f'\n{"#" * int(m[1])} {_strip_tags(m[2])}\n', text, flags=re.I)
        text = re.sub(r'<li[^>]*>([\s\S]*?)</li>', lambda m: f'\n- {_strip_tags(m[1])}', text, flags=re.I)
        text = re.sub(r'</(p|div|section|article)>', '\n\n', text, flags=re.I)
        text = re.sub(r'<(br|hr)\s*/?>', '\n', text, flags=re.I)
        return _normalize(_strip_tags(text))
