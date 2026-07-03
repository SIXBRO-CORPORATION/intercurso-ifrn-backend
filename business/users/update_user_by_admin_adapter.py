from typing import Optional

from core.business.users.update_user_by_admin_port import UpdateUserByAdminPort
from core.context import Context
from core.persistence.user_repository_port import UserRepositoryPort
from domain.enums.user_role import UserRole
from domain.exceptions.business_exception import BusinessException
from domain.user import User


class UpdateUserByAdminAdapter(UpdateUserByAdminPort):
    def __init__(self, user_repository: UserRepositoryPort):
        self.user_repository = user_repository

    async def execute(self, context: Context) -> User:
        target_user_id = context.get_property("target_user_id", object)
        name: Optional[str] = context.get_property("name", str)
        email: Optional[str] = context.get_property("email", str)
        role: Optional[UserRole] = context.get_property("role", UserRole)
        atleta: Optional[bool] = context.get_property("atleta", bool)
        active: Optional[bool] = context.get_property("active", bool)
        changed_by_user_id = context.get_property("changed_by_user_id", object)

        if target_user_id is None:
            raise BusinessException("Usuário alvo é obrigatório")

        target_user = await self.user_repository.get(target_user_id)
        if target_user is None:
            raise BusinessException("Usuário não encontrado")

        is_self_edit = target_user.id == changed_by_user_id
        if is_self_edit and role is not None and role != UserRole.ADMIN:
            raise BusinessException(
                "Você não pode remover o próprio papel de administrador"
            )
        if is_self_edit and active is False:
            raise BusinessException("Você não pode desativar a própria conta")

        if name is not None:
            if not name.strip():
                raise BusinessException("Nome não pode ser vazio")
            target_user.name = name.strip()

        if email is not None:
            if email != target_user.email and await self.user_repository.exists_by_email(
                email
            ):
                raise BusinessException("Já existe um usuário com esse e-mail")
            target_user.email = email

        if role is not None:
            target_user.role = role

        if atleta is not None:
            target_user.atleta = atleta

        if active is not None:
            target_user.active = active

        return await self.user_repository.save(target_user)
