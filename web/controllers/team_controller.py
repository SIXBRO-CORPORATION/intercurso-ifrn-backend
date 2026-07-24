from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, status
from fastapi.params import Depends

from core.business.team.approve_team_port import ApproveTeamPort
from core.business.team.confirm_donation_port import ConfirmDonationPort
from core.business.team.create_team_port import CreateTeamPort
from core.business.team.get_team_invite_info_port import GetTeamInviteInfoPort
from core.business.team.join_team_via_invite_port import JoinTeamViaInvitePort
from core.business.team.leave_team_port import LeaveTeamPort
from core.business.team.remove_member_port import RemoveMemberPort
from core.business.team.select_captain_port import SelectCaptainPort
from core.business.team.submit_team_port import SubmitTeamPort
from core.context import Context
from domain.modality import Modality
from domain.team import Team
from domain.team.team_member import TeamMember
from domain.user import User
from web.commons.api_response import ApiResponse
from web.mappers.team_model_mapper import TeamModelMapper
from web.models.request.team.team_register_request import TeamRegisterRequest
from web.models.response.team.team_invite_preview_response import (
    TeamInvitePreviewResponse,
)
from web.models.response.team.team_join_response import TeamJoinResponse
from web.models.response.team.team_register_response import TeamRegisterResponse
from web.dependencies import (
    get_create_team_port,
    get_approve_team_port,
    get_confirm_donation_team_port,
    get_team_invite_info_port,
    get_join_team_via_invite_port,
    get_select_captain_port,
    get_remove_member_port,
    get_leave_team_port,
    get_submit_team_port,
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
    "/{team_id}/submit",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
)
async def submit_team(
    team_id: UUID,
    submit_team_port: Annotated[SubmitTeamPort, Depends(get_submit_team_port)],
    current_user: User = Depends(require_authenticated_user),
):
    context = Context()
    context.put_property("team_id", team_id)
    context.put_property("requesting_user_id", current_user.id)

    submitted_team = await submit_team_port.execute(context)

    return ApiResponse.success(
        data={
            "team_id": str(submitted_team.id),
            "name": submitted_team.name,
            "status": submitted_team.status.value,
            "token_active": submitted_team.token_active,
            "submmited_at": (
                submitted_team.submmited_at.isoformat()
                if submitted_team.submmited_at
                else None
            ),
        },
        message="Time submetido para aprovação com sucesso! Aguarde a confirmação das doações e a aprovação do monitor.",
    )


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
    "/{team_id}/members/{user_id}/confirm-donation",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
)
async def confirm_donation(
    team_id: UUID,
    user_id: UUID,
    confirm_donation_port: Annotated[
        ConfirmDonationPort, Depends(get_confirm_donation_team_port)
    ],
    current_user: User = Depends(require_monitor),
):
    context = Context()
    context.put_property("team_id", team_id)
    context.put_property("target_user_id", user_id)
    context.put_property("confirmed_by_user_id", current_user.id)

    updated_member = await confirm_donation_port.execute(context)

    member_user = context.get_property("member_user", User)

    return ApiResponse.success(
        data={
            "member_user_id": str(user_id),
            "member_matricula": member_user.matricula if member_user else None,
            "member_name": member_user.name if member_user else None,
            "status": updated_member.donation_status.value,
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


@router.patch(
    "/{team_id}/members/{user_id}/captain",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
)
async def select_captain(
    team_id: UUID,
    user_id: UUID,
    select_captain_port: Annotated[
        SelectCaptainPort, Depends(get_select_captain_port)
    ],
    current_user: User = Depends(require_authenticated_user),
):
    context = Context()
    context.put_property("team_id", team_id)
    context.put_property("target_user_id", user_id)
    context.put_property("requesting_user_id", current_user.id)

    updated_team = await select_captain_port.execute(context)

    return ApiResponse.success(
        data={
            "team_id": str(updated_team.id),
            "captain_id": str(updated_team.captain_id),
            "is_owner": updated_team.owner_id == user_id,
            "is_captain": True,
        },
        message="Capitão selecionado com sucesso!",
    )


@router.delete(
    "/{team_id}/members/{user_id}",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
)
async def remove_member(
    team_id: UUID,
    user_id: UUID,
    remove_member_port: Annotated[RemoveMemberPort, Depends(get_remove_member_port)],
    current_user: User = Depends(require_authenticated_user),
):
    context = Context()
    context.put_property("team_id", team_id)
    context.put_property("target_user_id", user_id)
    context.put_property("requesting_user_id", current_user.id)

    await remove_member_port.execute(context)

    removed_user = context.get_property("removed_user", User)
    administrative_operation = (
        context.get_property("administrative_operation", bool) or False
    )

    return ApiResponse.success(
        data={
            "team_id": str(team_id),
            "user_id": str(user_id),
            "name": removed_user.name if removed_user else None,
            "matricula": removed_user.matricula if removed_user else None,
            "administrative_operation": administrative_operation,
        },
        message="Membro removido com sucesso!",
    )


@router.delete(
    "/{team_id}/leave",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
)
async def leave_team(
    team_id: UUID,
    leave_team_port: Annotated[LeaveTeamPort, Depends(get_leave_team_port)],
    current_user: User = Depends(require_authenticated_user),
):
    context = Context()
    context.put_property("team_id", team_id)
    context.put_property("requesting_user_id", current_user.id)

    await leave_team_port.execute(context)

    return ApiResponse.success(
        data={
            "team_id": str(team_id),
            "user_id": str(current_user.id),
        },
        message="Você saiu do time com sucesso!",
    )
