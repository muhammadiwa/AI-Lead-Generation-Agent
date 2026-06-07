import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_leads_unauthenticated(client: AsyncClient):
    """
    Verify that GET /leads returns 401 without auth
    """
    if client is None:
        pytest.skip("FastAPI app not yet scaffolded")
    
    response = await client.get("/api/v1/leads")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """
    Verify health check endpoint
    """
    if client is None:
        pytest.skip("FastAPI app not yet scaffolded")
        
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "success"}

@pytest.mark.asyncio
async def test_create_icp_profile_validation(client: AsyncClient):
    """
    Verify validation on POST /icp
    """
    if client is None:
        pytest.skip("FastAPI app not yet scaffolded")
        
    # Missing 'name' field
    data = {"description": "Test ICP"}
    response = await client.post("/api/v1/icp", json=data)
    assert response.status_code == 422
