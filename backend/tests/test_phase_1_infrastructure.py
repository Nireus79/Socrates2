"""
Phase 1 Infrastructure Tests

Comprehensive tests for:
- Database connections
- Models (BaseModel, User)
- Authentication (JWT)
- ServiceContainer
- BaseAgent
- AgentOrchestrator
- API endpoints
"""
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from jose import jwt
import uuid

from backend.app.core.config import settings
from backend.app.core.database import get_db_auth, get_db_specs, Base, engine_auth, engine_specs
from backend.app.core.security import create_access_token, decode_access_token
from backend.app.core.dependencies import ServiceContainer, reset_service_container
from backend.app.models.base import BaseModel
from backend.app.models.user import User
from backend.app.agents.base import BaseAgent
from backend.app.agents.orchestrator import AgentOrchestrator, reset_orchestrator
from backend.app.main import app


# Test client for API endpoints
client = TestClient(app)


class TestDatabaseConnections:
    """Test database connectivity"""

    def test_auth_database_connection(self):
        """Test can connect to auth database"""
        with engine_auth.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_specs_database_connection(self):
        """Test can connect to specs database"""
        with engine_specs.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_auth_database_has_users_table(self):
        """Test users table exists in auth database"""
        with engine_auth.connect() as conn:
            result = conn.execute(
                text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')")
            )
            assert result.scalar() == True


class TestUserModel:
    """Test User model functionality"""

    def test_create_user(self):
        """Test can create user instance"""
        user = User(
            email="test@example.com",
            hashed_password=User.hash_password("password123"),
            is_active=True,
            is_verified=False,
            status='active',
            role='user'
        )

        assert user.email == "test@example.com"
        assert user.is_active == True
        assert user.is_verified == False
        assert user.status == 'active'
        assert user.role == 'user'

    def test_password_hashing(self):
        """Test password hashing and verification"""
        plain_password = "SecurePassword123!"
        hashed = User.hash_password(plain_password)

        # Hashed password should be different from plain
        assert hashed != plain_password

        # Should be able to verify correct password
        user = User(
            email="test@example.com",
            hashed_password=hashed,
            is_active=True,
            is_verified=False,
            status='active',
            role='user'
        )

        assert user.verify_password(plain_password) == True
        assert user.verify_password("wrong_password") == False

    def test_user_to_dict_excludes_password(self):
        """Test to_dict() excludes hashed_password"""
        user = User(
            email="test@example.com",
            hashed_password=User.hash_password("password123"),
            is_active=True,
            is_verified=False,
            status='active',
            role='user'
        )

        user_dict = user.to_dict()

        assert 'email' in user_dict
        assert 'hashed_password' not in user_dict


class TestJWTAuthentication:
    """Test JWT token creation and validation"""

    def test_create_access_token(self):
        """Test JWT token creation"""
        user_id = str(uuid.uuid4())
        token = create_access_token(data={"sub": user_id})

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token(self):
        """Test JWT token decoding"""
        user_id = str(uuid.uuid4())
        token = create_access_token(data={"sub": user_id})

        payload = decode_access_token(token)

        assert payload is not None
        assert payload["sub"] == user_id
        assert "exp" in payload

    def test_invalid_token_raises_error(self):
        """Test invalid token raises exception"""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            decode_access_token("invalid.token.here")

        assert exc_info.value.status_code == 401


class TestServiceContainer:
    """Test ServiceContainer dependency injection"""

    def setup_method(self):
        """Reset container before each test"""
        reset_service_container()

    def test_create_service_container(self):
        """Test can create ServiceContainer"""
        services = ServiceContainer()
        assert services is not None

    def test_get_logger(self):
        """Test get_logger returns logger"""
        services = ServiceContainer()
        logger = services.get_logger("test")

        assert logger is not None
        assert logger.name == "test"

    def test_get_config(self):
        """Test get_config returns dict"""
        services = ServiceContainer()
        config = services.get_config()

        assert config is not None
        assert isinstance(config, dict)
        assert 'DATABASE_URL_AUTH' in config

    def test_get_database_auth(self):
        """Test get_database_auth returns session"""
        services = ServiceContainer()
        db = services.get_database_auth()

        assert db is not None
        # Should be able to execute query
        result = db.execute(text("SELECT 1"))
        assert result.scalar() == 1

        services.close()

    def test_get_database_specs(self):
        """Test get_database_specs returns session"""
        services = ServiceContainer()
        db = services.get_database_specs()

        assert db is not None
        # Should be able to execute query
        result = db.execute(text("SELECT 1"))
        assert result.scalar() == 1

        services.close()


class TestBaseAgent:
    """Test BaseAgent functionality"""

    def setup_method(self):
        """Reset containers before each test"""
        reset_service_container()

    def test_base_agent_requires_services(self):
        """Test BaseAgent raises error without ServiceContainer"""
        with pytest.raises(ValueError) as exc_info:
            class TestAgent(BaseAgent):
                def get_capabilities(self):
                    return ["test"]

            TestAgent("test", "Test Agent", None) # TODO Expected type 'None', got 'str' instead

        assert "ServiceContainer is required" in str(exc_info.value)

    def test_base_agent_with_services(self):
        """Test BaseAgent works with ServiceContainer"""
        services = ServiceContainer()

        class TestAgent(BaseAgent):
            def get_capabilities(self):
                return ["test_action"]

            def _test_action(self, data):
                return {'success': True, 'result': 'test'}

        agent = TestAgent("test", "Test Agent", services)

        assert agent.agent_id == "test"
        assert agent.name == "Test Agent"
        assert "test_action" in agent.get_capabilities()

    def test_agent_process_request(self):
        """Test agent request processing"""
        services = ServiceContainer()

        class TestAgent(BaseAgent):
            def get_capabilities(self):
                return ["create_item"]

            def _create_item(self, data):
                return {
                    'success': True,
                    'data': {'item_id': '123', 'name': data.get('name')}
                }

        agent = TestAgent("test", "Test", services)
        result = agent.process_request("create_item", {'name': 'Test Item'})

        assert result['success'] == True
        assert result['data']['item_id'] == '123'
        assert result['data']['name'] == 'Test Item'

    def test_agent_unknown_action(self):
        """Test agent returns error for unknown action"""
        services = ServiceContainer()

        class TestAgent(BaseAgent):
            def get_capabilities(self):
                return ["known_action"]

        agent = TestAgent("test", "Test", services)
        result = agent.process_request("unknown_action", {})

        assert result['success'] == False
        assert result['error_code'] == 'UNKNOWN_ACTION'

    def test_agent_statistics_tracking(self):
        """Test agent tracks statistics"""
        services = ServiceContainer()

        class TestAgent(BaseAgent):
            def get_capabilities(self):
                return ["test"]

            def _test(self, data):
                return {'success': True}

        agent = TestAgent("test", "Test", services)

        # Initial stats
        assert agent.stats['requests_processed'] == 0

        # Process request
        agent.process_request("test", {})

        # Stats updated
        assert agent.stats['requests_processed'] == 1
        assert agent.stats['requests_succeeded'] == 1


class TestAgentOrchestrator:
    """Test AgentOrchestrator functionality"""

    def setup_method(self):
        """Reset orchestrator before each test"""
        reset_orchestrator()
        reset_service_container()

    def test_create_orchestrator(self):
        """Test can create orchestrator"""
        services = ServiceContainer()
        orchestrator = AgentOrchestrator(services)

        assert orchestrator is not None
        assert len(orchestrator.agents) == 0

    def test_register_agent(self):
        """Test agent registration"""
        services = ServiceContainer()
        orchestrator = AgentOrchestrator(services)

        class TestAgent(BaseAgent):
            def get_capabilities(self):
                return ["test"]

        agent = TestAgent("test_agent", "Test Agent", services)
        orchestrator.register_agent(agent)

        assert "test_agent" in orchestrator.agents
        assert orchestrator.agents["test_agent"] == agent

    def test_register_non_agent_raises_error(self):
        """Test registering non-BaseAgent raises TypeError"""
        services = ServiceContainer()
        orchestrator = AgentOrchestrator(services)

        with pytest.raises(TypeError):
            orchestrator.register_agent("not an agent")  # TODO Expected type 'BaseAgent', got 'str' instead

    def test_route_request_to_agent(self):
        """Test routing request to registered agent"""
        services = ServiceContainer()
        orchestrator = AgentOrchestrator(services)

        class TestAgent(BaseAgent):
            def get_capabilities(self):
                return ["process"]

            def _process(self, data):
                return {'success': True, 'data': data}

        agent = TestAgent("test", "Test", services)
        orchestrator.register_agent(agent)

        result = orchestrator.route_request("test", "process", {'key': 'value'})

        assert result['success'] == True
        assert result['data']['key'] == 'value'

    def test_route_to_unknown_agent(self):
        """Test routing to unknown agent returns error"""
        services = ServiceContainer()
        orchestrator = AgentOrchestrator(services)

        result = orchestrator.route_request("nonexistent", "action", {})

        assert result['success'] == False
        assert result['error_code'] == 'UNKNOWN_AGENT'

    def test_route_unsupported_action(self):
        """Test routing unsupported action returns error"""
        services = ServiceContainer()
        orchestrator = AgentOrchestrator(services)

        class TestAgent(BaseAgent):
            def get_capabilities(self):
                return ["supported_action"]

        agent = TestAgent("test", "Test", services)
        orchestrator.register_agent(agent)

        result = orchestrator.route_request("test", "unsupported_action", {})

        assert result['success'] == False
        assert result['error_code'] == 'UNSUPPORTED_ACTION'


class TestAPIEndpoints:
    """Test API endpoints"""

    def test_root_endpoint(self):
        """Test root endpoint returns welcome message"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "Socrates2 API" in data['message']
        assert data['version'] == "0.1.0"

    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/api/v1/admin/health")

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['databases']['auth'] == 'connected'
        assert data['databases']['specs'] == 'connected'

    def test_api_info(self):
        """Test API info endpoint"""
        response = client.get("/api/v1/info")

        assert response.status_code == 200
        data = response.json()
        assert data['api']['version'] == "0.1.0"
        assert 'agents' in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
