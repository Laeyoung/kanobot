"""Tests for NaverSearchTool."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from kanobot.agent.tools.registry import ToolRegistry
from kanobot.agent.tools.web import NaverSearchTool
from kanobot.config.schema import NaverSearchConfig, WebToolsConfig

# ---------------------------------------------------------------------------
# Config / Schema tests
# ---------------------------------------------------------------------------


def test_naver_config_defaults():
    cfg = NaverSearchConfig()
    assert cfg.client_id == ""
    assert cfg.client_secret == ""
    assert cfg.max_results == 5


def test_naver_config_in_web_tools():
    web = WebToolsConfig()
    assert isinstance(web.naver, NaverSearchConfig)
    assert web.naver.client_id == ""


# ---------------------------------------------------------------------------
# Tool metadata tests
# ---------------------------------------------------------------------------


def test_tool_name_and_description():
    tool = NaverSearchTool()
    assert tool.name == "naver_search"
    assert "Korean" in tool.description


def test_tool_parameters_schema():
    tool = NaverSearchTool()
    props = tool.parameters["properties"]
    assert "query" in props
    assert "type" in props
    assert props["type"]["enum"] == ["web", "blog", "news", "encyc"]
    assert "count" in props
    assert "sort" in props
    assert tool.parameters["required"] == ["query"]


# ---------------------------------------------------------------------------
# Credential check
# ---------------------------------------------------------------------------


async def test_missing_credentials():
    tool = NaverSearchTool()
    result = await tool.execute(query="테스트")
    assert "Error" in result
    assert "credentials" in result.lower() or "client_id" in result.lower()


async def test_partial_credentials():
    tool = NaverSearchTool(client_id="id_only")
    result = await tool.execute(query="테스트")
    assert "Error" in result


# ---------------------------------------------------------------------------
# Invalid search type
# ---------------------------------------------------------------------------


async def test_invalid_search_type():
    tool = NaverSearchTool(client_id="test", client_secret="test")
    result = await tool.execute(query="테스트", type="image")
    assert "Invalid search type" in result


# ---------------------------------------------------------------------------
# Successful response (mocked)
# ---------------------------------------------------------------------------

NAVER_RESPONSE = {
    "lastBuildDate": "Mon, 01 Jan 2024 00:00:00 +0900",
    "total": 2,
    "start": 1,
    "display": 2,
    "items": [
        {
            "title": "<b>파이썬</b> 프로그래밍 입문",
            "link": "https://example.com/python",
            "description": "<b>파이썬</b>은 배우기 쉬운 &amp; 강력한 언어입니다.",
        },
        {
            "title": "Python &amp; Data Science",
            "link": "https://example.com/ds",
            "description": "데이터 과학을 위한 <b>파이썬</b>",
        },
    ],
}


def _mock_response(status_code=200, json_data=None):
    resp = httpx.Response(
        status_code=status_code,
        json=json_data or NAVER_RESPONSE,
        request=httpx.Request("GET", "https://openapi.naver.com/v1/search/webkr.json"),
    )
    return resp


async def test_successful_search():
    tool = NaverSearchTool(client_id="cid", client_secret="csec")
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_mock_response())
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("kanobot.agent.tools.web.httpx.AsyncClient", return_value=mock_client):
        result = await tool.execute(query="파이썬")

    assert "파이썬 프로그래밍 입문" in result  # HTML <b> stripped
    assert "<b>" not in result
    assert "&amp;" not in result  # HTML entities decoded
    assert "https://example.com/python" in result
    assert "https://example.com/ds" in result


async def test_html_tag_stripping():
    """Naver returns <b> tags around matched keywords — verify they're removed."""
    tool = NaverSearchTool(client_id="cid", client_secret="csec")
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_mock_response())
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("kanobot.agent.tools.web.httpx.AsyncClient", return_value=mock_client):
        result = await tool.execute(query="파이썬")

    # Should not contain any HTML tags
    assert "<" not in result or "https://" in result.replace("<", "")
    # The & entity should be decoded
    assert "쉬운 & 강력한" in result


# ---------------------------------------------------------------------------
# Search type → endpoint mapping
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "search_type,expected_path",
    [
        ("web", "/v1/search/webkr.json"),
        ("blog", "/v1/search/blog.json"),
        ("news", "/v1/search/news.json"),
        ("encyc", "/v1/search/encyc.json"),
    ],
)
async def test_endpoint_mapping(search_type, expected_path):
    tool = NaverSearchTool(client_id="cid", client_secret="csec")
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_mock_response())
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("kanobot.agent.tools.web.httpx.AsyncClient", return_value=mock_client):
        await tool.execute(query="테스트", type=search_type)

    url_called = mock_client.get.call_args[0][0]
    assert expected_path in url_called


# ---------------------------------------------------------------------------
# Empty results
# ---------------------------------------------------------------------------


async def test_empty_results():
    tool = NaverSearchTool(client_id="cid", client_secret="csec")
    empty_resp = _mock_response(json_data={"items": []})
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=empty_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("kanobot.agent.tools.web.httpx.AsyncClient", return_value=mock_client):
        result = await tool.execute(query="없는검색어xyz")

    assert "No results" in result


# ---------------------------------------------------------------------------
# Rate limit (429)
# ---------------------------------------------------------------------------


async def test_rate_limit_handling():
    tool = NaverSearchTool(client_id="cid", client_secret="csec")
    resp_429 = _mock_response(status_code=429, json_data={})
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=resp_429)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("kanobot.agent.tools.web.httpx.AsyncClient", return_value=mock_client):
        result = await tool.execute(query="테스트")

    assert "rate limit" in result.lower()


# ---------------------------------------------------------------------------
# HTTP error (non-429)
# ---------------------------------------------------------------------------


async def test_http_error():
    tool = NaverSearchTool(client_id="cid", client_secret="csec")
    resp_500 = httpx.Response(
        status_code=500,
        request=httpx.Request("GET", "https://openapi.naver.com/v1/search/webkr.json"),
    )
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=resp_500)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("kanobot.agent.tools.web.httpx.AsyncClient", return_value=mock_client):
        result = await tool.execute(query="테스트")

    assert "Error" in result
    assert "500" in result


# ---------------------------------------------------------------------------
# ToolRegistry integration
# ---------------------------------------------------------------------------


async def test_registry_integration():
    reg = ToolRegistry()
    tool = NaverSearchTool(client_id="cid", client_secret="csec")
    reg.register(tool)

    assert reg.get("naver_search") is tool

    defs = reg.get_definitions()
    names = [d["function"]["name"] for d in defs]
    assert "naver_search" in names
