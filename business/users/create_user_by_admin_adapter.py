from core.business.users.create_user_by_admin_port import CreateUserByAdminPort
from core.context import Context
from core.persistence.user_repository_port import UserRepositoryPort
from domain.enums.user_role import UserRole
from domain.exceptions.business_exception import BusinessException
from domain.user import User


class CreateUserByAdminAdapter(CreateUserByAdminPort):
    def __init__(self, user_repository: UserRepositoryPort):
        self.user_repository = user_repository

    async def execute(self, context: Context) -> User:
        user = context.get_data(User)
        role = context.get_property("role", UserRole)

        if user is None:
            raise BusinessException("Dados do usuário são obrigatórios")

        if role is None or role == UserRole.USER:
            raise BusinessException(
                "Usuários com papel USER são criados automaticamente no "
                "primeiro login via SUAP, não por este endpoint"
            )

        if not user.name or not user.name.strip():
            raise BusinessException("Nome é obrigatório")

        if user.matricula is None:
            raise BusinessException("Matrícula é obrigatória")

        if user.cpf is None:
            raise BusinessException("CPF é obrigatório")

        if await self.user_repository.exists_by_matricula(user.matricula):
            raise BusinessException("Já existe um usuário com essa matrícula")

        if user.cpf and await self.user_repository.exists_by_cpf(user.cpf):
            raise BusinessException("Já existe um usuário com esse CPF")

        if user.email and await self.user_repository.exists_by_email(user.email):
            raise BusinessException("Já existe um usuário com esse e-mail")

        new_user = User(
            name=user.name.strip(),
            email=user.email,
            cpf=user.cpf,
            matricula=user.matricula,
            atleta=False,
            active=True,
            role=role,
        )

        return await self.user_repository.save(new_user)
