from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, status
from fastapi.params import Depends

from core.business.team.approve_team_port import ApproveTeamPort
from core.business.team.confirm_donation_port import ConfirmDonationPort
from core.business.team.create_team_port import CreateTeamPort
from core.context import Context
from domain.team import Team
from web.commons.ApiResponse import ApiResponse
from web.mappers.team_model_mapper import TeamModelMapper
from web.models.request.team_register_request import TeamRegisterRequest
from web.models.response.team_register_response import TeamRegisterResponse
from web.dependencies import (
    get_create_team_port,
    get_approve_team_port,
    get_confirm_donation_port
)

router = APIRouter(prefix="/api/teams", tags=["teams"])

@router.post(
    "/",
    response_model=ApiResponse[TeamRegisterResponse],
    status_code=status.HTTP_201_CREATED
)
async def create_team(
        request: TeamRegisterRequest,
        create_team_port: Annotated[CreateTeamPort, Depends(get_create_team_port)]
):

    team_domain = Team(
        name = request.name,
        photo = request.photo,
        modality = request.modality
    )

    context = Context(data=team_domain)
    context.put_property("members", [member.model_dump() for member in request.members])

    saved_team = await create_team_port.execute(context)

    team_members = context.get_property("team_members", list)

    mapper = TeamModelMapper()
    response_data = mapper.to_register_response(saved_team, team_members)

    return ApiResponse(
        data=response_data,
        message="Time cadastrado com sucesso!"
    )

@router.patch(
    "/{team_id}/approve",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK
)
async def approve_team(
        team_id: UUID,
        approve_team_port: Annotated[ApproveTeamPort, Depends(get_approve_team_port)]
):
    context = Context()
    context.put_property("team_id", team_id)

    approved_team = await approve_team_port.execute(context)

    return ApiResponse.success(
        data={
            "team_id": str(approved_team.id),
            "name": approved_team.name,
            "status": approved_team.status.value,
            "modality": approved_team.modality.value
        },
        message="Time aprovado com sucesso!"
    )

@router.patch(
    "/{team_id}/members/{matricula}/confirm-donation",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK
)
async def confirm_donation(
        team_id: UUID,
        matricula: int,
        confirm_donation_port: Annotated[ConfirmDonationPort, Depends(get_confirm_donation_port)]
):

    context = Context()
    context.put_property("team_id", team_id)
    context.put_property("matricula", matricula)

    updated_member = await confirm_donation_port.execute(context)

    user_updated = context.get_property("user_updated", bool)

    return ApiResponse.success(
        data={
            "member_matricula": updated_member.member_matricula,
            "member_name": updated_member.member_name,
            "status": updated_member.status.value,
            "user_updated": user_updated
        },
        message="Doação confirmada com sucesso!"
    )