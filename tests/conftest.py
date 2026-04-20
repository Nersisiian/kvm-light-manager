import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from app.db.base import Base
from app.main import app
from app.services.redis_client import redis_client
from app.services.agent_client import init_agent_client
from app.messaging.client import ZeroMQClient
from app.core.config import settings


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    with PostgresContainer("postgres:15-alpine") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def redis_container() -> Generator[RedisContainer, None, None]:
    with RedisContainer("redis:7-alpine") as redis:
        yield redis


@pytest.fixture(scope="session")
async def test_db_engine(postgres_container):
    db_url = postgres_container.get_connection_url().replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(db_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    connection = await test_db_engine.connect()
    transaction = await connection.begin()
    session = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
    )()
    yield session
    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest_asyncio.fixture(autouse=True)
async def override_dependencies(db_session, redis_container):
    app.dependency_overrides = {}

    async def override_get_db():
        yield db_session
    from app.api.dependencies import get_db
    app.dependency_overrides[get_db] = override_get_db

    test_redis_url = f"redis://{redis_container.get_container_host_ip()}:{redis_container.get_exposed_port(6379)}"
    settings.REDIS_HOST = redis_container.get_container_host_ip()
    settings.REDIS_PORT = redis_container.get_exposed_port(6379)
    await redis_client.initialize()
    yield
    await redis_client.close()


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_zmq_client(mocker):
    mock = mocker.AsyncMock(spec=ZeroMQClient)
    mock.send_request.return_value = b'{"request_id":"test","status":"success"}'
    init_agent_client(mock)
    return mock