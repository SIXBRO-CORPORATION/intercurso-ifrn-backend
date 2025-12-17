# tests/unit/business/auth/test_login_with_suap_adapter.py

import pytest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4
from datetime import datetime, timedelta
from security.adapters.login_suap_adapter import LoginWithSUAPAdapter
from domain.auth_token import SUAPUserData, AuthToken
from domain.user import User


@pytest.fixture
def mock_oauth_provider():
    return AsyncMock()


@pytest.fixture
def mock_token_service():
    mock = Mock()
    mock.create_access_token.return_value = AuthToken(
        access_token="fake_token",
        token_type="bearer",
        expires_at=datetime.utcnow() + timedelta(hours=1),
        user_id=uuid4()
    )
    return mock


@pytest.fixture
def mock_user_repository():
    return AsyncMock()


@pytest.fixture
def login_adapter(mock_oauth_provider, mock_token_service, mock_user_repository):
    return LoginWithSUAPAdapter(
        oauth_provider=mock_oauth_provider,
        token_service=mock_token_service,
        user_repository=mock_user_repository
    )


@pytest.mark.asyncio
async def test_login_new_user_success(login_adapter, mock_oauth_provider, mock_user_repository):
    # Arrange
    suap_data = SUAPUserData(
        matricula="20231234567",
        nome_usual="João Silva",
        email="joao@example.com",
        cpf="12345678900",
        tipo_usuario="Aluno",
        campus="Campus Central",
        curso="TSI",
        vinculo={}
    )

    mock_oauth_provider.authenticate_with_code.return_value = suap_data
    mock_user_repository.find_by_matricula.return_value = None

    new_user = User(
        id=uuid4(),
        name="João Silva",
        email="joao@example.com",
        cpf=12345678900,
        matricula=20231234567,
        active=True
    )
    mock_user_repository.save.return_value = new_user

    # Act
    token = await login_adapter.execute("auth_code_123")

    # Assert
    assert token.access_token == "fake_token"
    mock_user_repository.save.assert_called_once()