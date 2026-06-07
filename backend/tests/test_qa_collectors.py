import pytest
from app.collectors.github import GitHubCollector
from app.collectors.base import CollectedLead

@pytest.mark.asyncio
async def test_github_collector_search_success(mocker):
    # Mock response data
    mock_items = [
        {
            "id": 12345,
            "full_name": "testorg/testrepo",
            "owner": {
                "login": "testorg",
                "type": "Organization",
                "html_url": "https://github.com/testorg"
            },
            "html_url": "https://github.com/testorg/testrepo",
            "description": "A test repository",
            "language": "Python",
            "topics": ["python", "react"]
        }
    ]
    
    # Mock httpx.AsyncClient.get
    mock_resp = mocker.Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"items": mock_items}
    
    # We need to mock the client context manager
    mock_client = mocker.AsyncMock()
    mock_client.get.return_value = mock_resp
    mocker.patch("httpx.AsyncClient", return_value=mock_client)
    mocker.patch("httpx.AsyncClient.__aenter__", return_value=mock_client)
    
    # Mock utils to avoid delays in tests
    mocker.patch("app.collectors.github.async_random_delay", return_value=None)
    mocker.patch("app.collectors.github.rate_limiter.wait", return_value=None)

    collector = GitHubCollector()
    results = await collector.search(query={"topics": ["python"]}, max_results=1)
    
    assert len(results) == 1
    lead = results[0]
    assert isinstance(lead, CollectedLead)
    assert lead.company_name == "testorg"
    assert lead.tech_stack["primary_language"] == "Python"
    assert lead.source == "github"

@pytest.mark.asyncio
async def test_github_collector_skips_individuals(mocker):
    mock_items = [
        {
            "id": 67890,
            "owner": {
                "login": "testuser",
                "type": "User",
                "html_url": "https://github.com/testuser"
            }
        }
    ]
    
    mock_resp = mocker.Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"items": mock_items}
    
    mock_client = mocker.AsyncMock()
    mock_client.get.return_value = mock_resp
    mocker.patch("httpx.AsyncClient", return_value=mock_client)
    mocker.patch("httpx.AsyncClient.__aenter__", return_value=mock_client)
    
    mocker.patch("app.collectors.github.async_random_delay", return_value=None)
    mocker.patch("app.collectors.github.rate_limiter.wait", return_value=None)

    collector = GitHubCollector()
    results = await collector.search(query={"topics": ["python"]}, max_results=1)
    
    # Should skip "User" owner type
    assert len(results) == 0

@pytest.mark.asyncio
async def test_github_collector_handles_api_failure(mocker):
    mock_resp = mocker.Mock()
    mock_resp.status_code = 403 # Rate limit or Auth error
    
    mock_client = mocker.AsyncMock()
    mock_client.get.return_value = mock_resp
    mocker.patch("httpx.AsyncClient", return_value=mock_client)
    mocker.patch("httpx.AsyncClient.__aenter__", return_value=mock_client)
    
    mocker.patch("app.collectors.github.async_random_delay", return_value=None)
    mocker.patch("app.collectors.github.rate_limiter.wait", return_value=None)

    collector = GitHubCollector()
    results = await collector.search(query={"topics": ["python"]}, max_results=1)
    
    assert len(results) == 0
