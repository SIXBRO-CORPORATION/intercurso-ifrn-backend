from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, status
from fastapi.params import Depends

from core.business.users.create_user_by_admin_port import CreateUserByAdminPort
from core.business.users.update_user_by_admin_port import UpdateUserByAdminPort
from core.context import Context
from domain.enums.user_role import UserRole
from domain.user import User
from web.commons.api_response import ApiResponse
from web.dependencies import (
    get_create_user_by_admin_port,
    get_update_user_by_admin_port,
    get_user_model_mapper,
    require_admin,
)
from web.mappers.user_model_mapper import UserModelMapper
from web.models.request.admin.admin_create_user_request import AdminCreateUserRequest
from web.models.request.admin.admin_update_user_request import AdminUpdateUserRequest
from web.models.response.user.user_response import UserResponse


router = APIRouter(prefix="/api/user", tags=["user"])


@router.post(
    "/",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    request: AdminCreateUserRequest,
    create_user_by_admin_port: Annotated[
        CreateUserByAdminPort, Depends(get_create_user_by_admin_port)
    ],
    mapper: Annotated[UserModelMapper, Depends(get_user_model_mapper)],
    current_user: User = Depends(require_admin),
):
    user_domain = User(
        name=request.name,
        email=request.email,
        cpf=request.cpf,
        matricula=request.matricula,
    )

    context = Context(data=user_domain)
    context.put_property("role", UserRole[request.role])
    context.put_property("created_by_user_id", current_user.id)

    saved_user = await create_user_by_admin_port.execute(context)

    return ApiResponse(
        data=mapper.to_response(saved_user), message="Usuário criado com sucesso!"
    )


@router.patch(
    "/{user_id}",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_200_OK,
)
async def update_user(
    user_id: UUID,
    request: AdminUpdateUserRequest,
    update_user_by_admin_port: Annotated[
        UpdateUserByAdminPort, Depends(get_update_user_by_admin_port)
    ],
    mapper: Annotated[UserModelMapper, Depends(get_user_model_mapper)],
    current_user: User = Depends(require_admin),
):
    context = Context()
    context.put_property("target_user_id", user_id)
    context.put_property("name", request.name)
    context.put_property("email", request.email)
    context.put_property("role", UserRole[request.role] if request.role else None)
    context.put_property("atleta", request.atleta)
    context.put_property("active", request.active)
    context.put_property("changed_by_user_id", current_user.id)

    updated_user = await update_user_by_admin_port.execute(context)

    return ApiResponse(
        data=mapper.to_response(updated_user), message="Usuário atualizado com sucesso!"
    )
