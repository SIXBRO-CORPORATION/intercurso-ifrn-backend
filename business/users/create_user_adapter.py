from core.business.users.create_user_port import CreateUserPort
from core.context import Context
from core.persistence.user_repository_port import UserRepositoryPort
from domain.user import User
from datetime import datetime


class CreateUserAdapter(CreateUserPort):
    def __init__(self, repository: UserRepositoryPort):
        self.repository = repository

    async def execute(self, context: Context) -> User:
        user = context.get_data(User)

        if user is None:
            raise RuntimeError("User data is required")

        if user.matricula is None:
            raise RuntimeError("Matricula is required")

        if user.cpf is None:
            raise RuntimeError("CPF is required")

        if await self.repository.exists_by_matricula(user.matricula):
            raise RuntimeError("Matricula already exists") # Trocar para Business Exception (aparece para usuário)

        new_user = User(
            name=user.name,
            email=user.email,
            cpf=user.cpf,
            matricula=user.matricula,
            created_at=datetime.now(),
            modified_at=None,
            atleta=False,
            active=True
        )

        saved_user = await self.repository.save(new_user)

        context.put_property("user_created", True)
        context.put_property("user_id", saved_user.id)

        return saved_user