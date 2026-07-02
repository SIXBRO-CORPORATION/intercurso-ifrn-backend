from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, status
from fastapi.params import Depends

from core.business.team.approve_team_port import ApproveTeamPort
from core.business.team.confirm_donation_port import ConfirmDonationPort
from core.business.team.create_team_port import CreateTeamPort
from core.context import Context
from domain.team import Team
from domain.team_member import TeamMember
from domain.user import User
from web.commons.ApiResponse import ApiResponse
from web.mappers.team_model_mapper import TeamModelMapper
from web.models.request.team_register_request import TeamRegisterRequest
from web.models.response.team_register_response import TeamRegisterResponse
from web.dependencies import (
    get_create_team_port,
    get_approve_team_port,
    get_confirm_donation_team_port,
    require_authenticated_user,
)


router = APIRouter(prefix="/api/teams", tags=["teams"])


@router.post(
    "/",
    response_model=ApiResponse[TeamRegisterResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_team(
    request: TeamRegisterRequest,
    create_team_port: Annotated[CreateTeamPort, Depends(get_create_team_port)],
    current_user: User = Depends(require_authenticated_user),
):
    team_domain = Team(
        name=request.name, photo=request.photo, modality_id=request.modality_id
    )

    context = Context(data=team_domain)
    context.put_property("creator_user_id", current_user.id)

    saved_team = await create_team_port.execute(context)

    owner_member = context.get_property("owner_member", TeamMember)

    mapper = TeamModelMapper()
    response_data = mapper.to_register_response(saved_team, owner_member, current_user)

    return ApiResponse(data=response_data, message="Time cadastrado com sucesso!")


@router.patch(
    "/{team_id}/approve",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
)
async def approve_team(
    team_id: UUID,
    approve_team_port: Annotated[ApproveTeamPort, Depends(get_approve_team_port)],
    current_user: User = Depends(require_authenticated_user),
):
    context = Context()
    context.put_property("team_id", team_id)
    context.put_property("approved_by_user_id", current_user.id)

    approved_team = await approve_team_port.execute(context)

    return ApiResponse.success(
        data={
            "team_id": str(approved_team.id),
            "name": approved_team.name,
            "status": approved_team.status.value,
            "modality_id": str(approved_team.modality_id),
        },
        message="Time aprovado com sucesso!",
    )


@router.patch(
    "/{team_id}/members/{matricula}/confirm-donation",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
)
async def confirm_donation(
    team_id: UUID,
    matricula: int,
    confirm_donation_port: Annotated[
        ConfirmDonationPort, Depends(get_confirm_donation_team_port)
    ],
    current_user: User = Depends(require_authenticated_user),
):
    context = Context()
    context.put_property("team_id", team_id)
    context.put_property("matricula", matricula)
    context.put_property("confirmed_by_user_id", current_user.id)

    updated_member = await confirm_donation_port.execute(context)

    user_updated = context.get_property("user_updated", bool)
    member_user = context.get_property("member_user", User)

    return ApiResponse.success(
        data={
            "member_matricula": member_user.matricula if member_user else matricula,
            "member_name": member_user.name if member_user else None,
            "status": updated_member.donation_status.value,
            "user_updated": bool(user_updated),
        },
        message="Doação confirmada com sucesso!",
    )
