from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, status
from fastapi.params import Depends

from core.business.team.approve_team_port import ApproveTeamPort
from core.business.team.confirm_donation_port import ConfirmDonationPort
from core.business.team.create_team_port import CreateTeamPort
from core.business.team.get_team_invite_info_port import GetTeamInviteInfoPort
from core.business.team.join_team_via_invite_port import JoinTeamViaInvitePort
from core.context import Context
from domain.modality import Modality
from domain.team import Team
from domain.team_member import TeamMember
from domain.user import User
from web.commons.api_response import ApiResponse
from web.mappers.team_model_mapper import TeamModelMapper
from web.models.request.team_register_request import TeamRegisterRequest
from web.models.response.team_invite_preview_response import (
    TeamInvitePreviewResponse,
)
from web.models.response.team_join_response import TeamJoinResponse
from web.models.response.team_register_response import TeamRegisterResponse
from web.dependencies import (
    get_create_team_port,
    get_approve_team_port,
    get_confirm_donation_team_port,
    get_team_invite_info_port,
    get_join_team_via_invite_port,
    get_team_model_mapper,
    require_authenticated_user,
    require_monitor,
)


router = APIRouter(prefix="/api/team", tags=["team"])


@router.post(
    "/",
    response_model=ApiResponse[TeamRegisterResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_team(
    request: TeamRegisterRequest,
    create_team_port: Annotated[CreateTeamPort, Depends(get_create_team_port)],
    mapper: Annotated[TeamModelMapper, Depends(get_team_model_mapper)],
    current_user: User = Depends(require_authenticated_user),
):
    team_domain = Team(
        name=request.name, photo=request.photo, modality_id=request.modality_id
    )

    context = Context(data=team_domain)
    context.put_property("creator_user_id", current_user.id)

    saved_team = await create_team_port.execute(context)

    owner_member = context.get_property("owner_member", TeamMember)

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
    current_user: User = Depends(require_monitor),
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
    current_user: User = Depends(require_monitor),
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


@router.get(
    "/invite/{invite_token}",
    response_model=ApiResponse[TeamInvitePreviewResponse],
    status_code=status.HTTP_200_OK,
)
async def get_team_invite_info(
    invite_token: str,
    invite_info_port: Annotated[
        GetTeamInviteInfoPort, Depends(get_team_invite_info_port)
    ],
    mapper: Annotated[TeamModelMapper, Depends(get_team_model_mapper)],
    current_user: User = Depends(require_authenticated_user),
):
    context = Context()
    context.put_property("invite_token", invite_token)
    context.put_property("requesting_user_id", current_user.id)

    team = await invite_info_port.execute(context)

    modality = context.get_property("modality", Modality)
    members_count = context.get_property("members_count", int) or 0
    owner_user = context.get_property("owner_user", User)
    captain_user = context.get_property("captain_user", User)

    response_data = mapper.to_invite_preview_response(
        team, modality, members_count, owner_user, captain_user
    )

    return ApiResponse(data=response_data, message="Informações do time carregadas com sucesso!")


@router.post(
    "/invite/{invite_token}/join",
    response_model=ApiResponse[TeamJoinResponse],
    status_code=status.HTTP_200_OK,
)
async def join_team_via_invite(
    invite_token: str,
    join_invite_port: Annotated[
        JoinTeamViaInvitePort, Depends(get_join_team_via_invite_port)
    ],
    mapper: Annotated[TeamModelMapper, Depends(get_team_model_mapper)],
    current_user: User = Depends(require_authenticated_user),
):
    context = Context()
    context.put_property("invite_token", invite_token)
    context.put_property("requesting_user_id", current_user.id)

    saved_member = await join_invite_port.execute(context)

    team = context.get_property("team", Team)

    response_data = mapper.to_join_response(team, saved_member)

    return ApiResponse(data=response_data, message="Você entrou no time com sucesso!")
