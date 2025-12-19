import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4


@pytest.fixture(scope="session")
def event_loop():
    """Cria event loop para testes assíncronos"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_suap_data():
    """Dados de exemplo do SUAP para reutilizar em vários testes"""
    from domain.auth_token import SUAPUserData

    return SUAPUserData(
        matricula="20231234567",
        nome_usual="João Silva",
        email="joao.silva@example.com",
        cpf="12345678900",
        tipo_usuario="Aluno",
        campus="Campus Central",
        curso="Tecnologia em Sistemas",
        vinculo={"curso": "TSI"}
    )


@pytest.fixture
def sample_user():
    """Usuário de exemplo para testes"""
    from domain.user import User

    return User(
        id=uuid4(),
        name="João Silva",
        email="joao@example.com",
        cpf=12345678900,
        matricula=20231234567,
        active=True
    )