from typing import Annotated
from fastapi import Depends

from core.business.audit.audit_logger import AuditLogger
from core.business.team.create_team_port import CreateTeamPort
from core.business.team.approve_team_port import ApproveTeamPort
from core.business.team.confirm_donation_port import ConfirmDonationPort
from core.business.team.get_team_invite_info_port import GetTeamInviteInfoPort
from core.business.team.join_team_via_invite_port import JoinTeamViaInvitePort
from core.business.team.select_captain_port import SelectCaptainPort
from core.business.team.remove_member_port import RemoveMemberPort
from core.business.team.leave_team_port import LeaveTeamPort
from core.business.team.submit_team_port import SubmitTeamPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from core.persistence.team.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from core.persistence.season.season_repository_port import SeasonRepositoryPort
from core.persistence.season.season_modality_repository_port import (
    SeasonModalityRepositoryPort,
)
from core.persistence.modality.modality_repository_port import ModalityRepositoryPort
from business.team.create_team_adapter import CreateTeamAdapter
from business.team.approve_team_adapter import ApproveTeamAdapter
from business.team.confirm_donation_adapter import ConfirmDonationAdapter
from business.team.get_team_invite_info_adapter import GetTeamInviteInfoAdapter
from business.team.join_team_via_invite_adapter import JoinTeamViaInviteAdapter
from business.team.select_captain_adapter import SelectCaptainAdapter
from business.team.remove_member_adapter import RemoveMemberAdapter
from business.team.leave_team_adapter import LeaveTeamAdapter
from business.team.submit_team_adapter import SubmitTeamAdapter
from web.dependencies.commons_dependencies import get_audit_logger
from web.dependencies.persistence_dependencies import (
    get_user_repository,
    get_team_repository,
    get_team_member_repository,
    get_season_repository,
    get_season_modality_repository,
    get_modality_repository,
)


def get_create_team_port(
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    team_member_repository: Annotated[
        TeamMemberRepositoryPort, Depends(get_team_member_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    season_repository: Annotated[SeasonRepositoryPort, Depends(get_season_repository)],
    season_modality_repository: Annotated[
        SeasonModalityRepositoryPort, Depends(get_season_modality_repository)
    ],
    modality_repository: Annotated[
        ModalityRepositoryPort, Depends(get_modality_repository)
    ],
) -> CreateTeamPort:
    return CreateTeamAdapter(
        team_repository,
        team_member_repository,
        user_repository,
        season_repository,
        season_modality_repository,
        modality_repository,
    )


def get_approve_team_port(
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    team_member_repository: Annotated[
        TeamMemberRepositoryPort, Depends(get_team_member_repository)
    ],
) -> ApproveTeamPort:
    return ApproveTeamAdapter(team_repository, team_member_repository)


def get_confirm_donation_team_port(
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    team_member_repository: Annotated[
        TeamMemberRepositoryPort, Depends(get_team_member_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
) -> ConfirmDonationPort:
    return ConfirmDonationAdapter(
        team_repository, team_member_repository, user_repository
    )


def get_team_invite_info_port(
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    team_member_repository: Annotated[
        TeamMemberRepositoryPort, Depends(get_team_member_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    season_repository: Annotated[SeasonRepositoryPort, Depends(get_season_repository)],
    modality_repository: Annotated[
        ModalityRepositoryPort, Depends(get_modality_repository)
    ],
) -> GetTeamInviteInfoPort:
    return GetTeamInviteInfoAdapter(
        team_repository,
        team_member_repository,
        user_repository,
        season_repository,
        modality_repository,
    )


def get_join_team_via_invite_port(
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    team_member_repository: Annotated[
        TeamMemberRepositoryPort, Depends(get_team_member_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    season_repository: Annotated[SeasonRepositoryPort, Depends(get_season_repository)],
    modality_repository: Annotated[
        ModalityRepositoryPort, Depends(get_modality_repository)
    ],
    audit_logger: Annotated[AuditLogger, Depends(get_audit_logger)],
) -> JoinTeamViaInvitePort:
    return JoinTeamViaInviteAdapter(
        team_repository,
        team_member_repository,
        user_repository,
        season_repository,
        modality_repository,
        audit_logger,
    )


def get_select_captain_port(
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    team_member_repository: Annotated[
        TeamMemberRepositoryPort, Depends(get_team_member_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    audit_logger: Annotated[AuditLogger, Depends(get_audit_logger)],
) -> SelectCaptainPort:
    return SelectCaptainAdapter(
        team_repository, team_member_repository, user_repository, audit_logger
    )


def get_remove_member_port(
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    team_member_repository: Annotated[
        TeamMemberRepositoryPort, Depends(get_team_member_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    audit_logger: Annotated[AuditLogger, Depends(get_audit_logger)],
) -> RemoveMemberPort:
    return RemoveMemberAdapter(
        team_repository, team_member_repository, user_repository, audit_logger
    )


def get_leave_team_port(
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    team_member_repository: Annotated[
        TeamMemberRepositoryPort, Depends(get_team_member_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    audit_logger: Annotated[AuditLogger, Depends(get_audit_logger)],
) -> LeaveTeamPort:
    return LeaveTeamAdapter(
        team_repository, team_member_repository, user_repository, audit_logger
    )


def get_submit_team_port(
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    team_member_repository: Annotated[
        TeamMemberRepositoryPort, Depends(get_team_member_repository)
    ],
    season_repository: Annotated[SeasonRepositoryPort, Depends(get_season_repository)],
    modality_repository: Annotated[
        ModalityRepositoryPort, Depends(get_modality_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    audit_logger: Annotated[AuditLogger, Depends(get_audit_logger)],
) -> SubmitTeamPort:
    return SubmitTeamAdapter(
        team_repository,
        team_member_repository,
        season_repository,
        modality_repository,
        user_repository,
        audit_logger,
    )