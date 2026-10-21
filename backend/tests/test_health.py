import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import engine, Base


@pytest.fixture(autouse=True)
def setup_db():
    import asyncio
    async def create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    asyncio.run(create_tables())
    yield
    async def drop_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    asyncio.run(drop_tables())


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health_check(client):
    async with client as ac:
        response = await ac.get("/health/")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_db_health_check(client):
    async with client as ac:
        response = await ac.get("/health/db")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["database"] == "connected"


@pytest.mark.asyncio
async def test_root(client):
    async with client as ac:
        response = await ac.get("/")
        assert response.status_code == 200
        assert response.json()["name"] == "axiom-engine"
        assert response.json()["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_create_and_list_keys(client):
    async with client as ac:
        response = await ac.post(
            "/v1/keys",
            json={
                "platform": "openai",
                "key_hash": "test-key-123",
                "key_name": "Test Key",
                "quota_limit": 1000,
            },
        )
        assert response.status_code == 201
        key_data = response.json()
        assert key_data["platform"] == "openai"
        assert key_data["key_name"] == "Test Key"

        response = await ac.get("/v1/keys")
        assert response.status_code == 200
        keys = response.json()
        assert len(keys) == 1
        assert keys[0]["id"] == key_data["id"]


@pytest.mark.asyncio
async def test_list_models_empty(client):
    async with client as ac:
        response = await ac.get("/v1/models")
        assert response.status_code == 200
        data = response.json()
        assert data["models"] == []
        assert data["total"] == 0


@pytest.mark.asyncio
async def test_chat_completions_no_model(client):
    async with client as ac:
        response = await ac.post(
            "/v1/chat/completions",
            json={"model": "openai/gpt-4o", "messages": [{"role": "user", "content": "Hello"}]},
        )
        assert response.status_code == 404
        assert "No enabled model found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_key_with_models(client):
    async with client as ac:
        key_response = await ac.post(
            "/v1/keys",
            json={"platform": "openai", "key_hash": "test-key-del-123", "key_name": "Delete Test"},
        )
        key_id = key_response.json()["id"]

        response = await ac.delete(f"/v1/keys/{key_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

        response = await ac.get("/v1/keys")
        assert len(response.json()) == 0