from typing import Annotated
from fastapi import Depends

from core.business.match.start_match_port import StartMatchPort
from core.business.match.register_goal_port import RegisterGoalPort
from core.business.match.register_card_port import RegisterCardPort
from core.business.match.pause_clock_port import PauseClockPort
from core.business.match.resume_clock_port import ResumeClockPort
from core.business.match.end_period_port import EndPeriodPort
from core.business.match.start_period_port import StartPeriodPort
from core.business.match.end_set_port import EndSetPort
from core.persistence.bracket_repository_port import BracketRepositoryPort
from core.persistence.match_event_repository_port import MatchEventRepositoryPort
from core.persistence.match_repository_port import MatchRepositoryPort
from core.persistence.modality_configuration_repository_port import (
    ModalityConfigurationRepositoryPort,
)
from core.persistence.modality_repository_port import ModalityRepositoryPort
from core.persistence.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team_repository_port import TeamRepositoryPort
from core.persistence.user_repository_port import UserRepositoryPort
from core.persistence.volleyball_modality_configuration_repository_port import (
    VolleyballModalityConfigurationRepositoryPort,
)
from core.persistence.match_set_repository_port import MatchSetRepositoryPort
from business.match.start_match_adapter import StartMatchAdapter
from business.match.register_goal_adapter import RegisterGoalAdapter
from business.match.register_card_adapter import RegisterCardAdapter
from business.match.pause_clock_adapter import PauseClockAdapter
from business.match.resume_clock_adapter import ResumeClockAdapter
from business.match.end_period_adapter import EndPeriodAdapter
from business.match.start_period_adapter import StartPeriodAdapter
from business.match.end_set_adapter import EndSetAdapter
from web.dependencies.persistence_dependencies import (
    get_bracket_repository,
    get_match_event_repository,
    get_match_repository,
    get_match_set_repository,
    get_modality_configuration_repository,
    get_modality_repository,
    get_team_member_repository,
    get_team_repository,
    get_user_repository,
    get_volleyball_modality_configuration_repository,
)


def get_start_match_port(
    match_repository: Annotated[MatchRepositoryPort, Depends(get_match_repository)],
    match_event_repository: Annotated[
        MatchEventRepositoryPort, Depends(get_match_event_repository)
    ],
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    team_member_repository: Annotated[
        TeamMemberRepositoryPort, Depends(get_team_member_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    bracket_repository: Annotated[BracketRepositoryPort, Depends(get_bracket_repository)],
    modality_configuration_repository: Annotated[
        ModalityConfigurationRepositoryPort,
        Depends(get_modality_configuration_repository),
    ],
    modality_repository: Annotated[
        ModalityRepositoryPort, Depends(get_modality_repository)
    ],
    volleyball_modality_configuration_repository: Annotated[
        VolleyballModalityConfigurationRepositoryPort,
        Depends(get_volleyball_modality_configuration_repository),
    ],
    match_set_repository: Annotated[
        MatchSetRepositoryPort, Depends(get_match_set_repository)
    ],
) -> StartMatchPort:
    return StartMatchAdapter(
        match_repository,
        match_event_repository,
        team_repository,
        team_member_repository,
        user_repository,
        bracket_repository,
        modality_configuration_repository,
        modality_repository,
        volleyball_modality_configuration_repository,
        match_set_repository,
    )


def get_register_goal_port(
    match_repository: Annotated[MatchRepositoryPort, Depends(get_match_repository)],
    match_event_repository: Annotated[
        MatchEventRepositoryPort, Depends(get_match_event_repository)
    ],
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    team_member_repository: Annotated[
        TeamMemberRepositoryPort, Depends(get_team_member_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    bracket_repository: Annotated[BracketRepositoryPort, Depends(get_bracket_repository)],
    modality_repository: Annotated[
        ModalityRepositoryPort, Depends(get_modality_repository)
    ],
    modality_configuration_repository: Annotated[
        ModalityConfigurationRepositoryPort,
        Depends(get_modality_configuration_repository),
    ],
    volleyball_modality_configuration_repository: Annotated[
        VolleyballModalityConfigurationRepositoryPort,
        Depends(get_volleyball_modality_configuration_repository),
    ],
    match_set_repository: Annotated[
        MatchSetRepositoryPort, Depends(get_match_set_repository)
    ],
) -> RegisterGoalPort:
    return RegisterGoalAdapter(
        match_repository,
        match_event_repository,
        team_repository,
        team_member_repository,
        user_repository,
        bracket_repository,
        modality_repository,
        modality_configuration_repository,
        volleyball_modality_configuration_repository,
        match_set_repository,
    )


def get_register_card_port(
    match_repository: Annotated[MatchRepositoryPort, Depends(get_match_repository)],
    match_event_repository: Annotated[
        MatchEventRepositoryPort, Depends(get_match_event_repository)
    ],
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    team_member_repository: Annotated[
        TeamMemberRepositoryPort, Depends(get_team_member_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    bracket_repository: Annotated[BracketRepositoryPort, Depends(get_bracket_repository)],
    modality_repository: Annotated[
        ModalityRepositoryPort, Depends(get_modality_repository)
    ],
    modality_configuration_repository: Annotated[
        ModalityConfigurationRepositoryPort,
        Depends(get_modality_configuration_repository),
    ],
    volleyball_modality_configuration_repository: Annotated[
        VolleyballModalityConfigurationRepositoryPort,
        Depends(get_volleyball_modality_configuration_repository),
    ],
    match_set_repository: Annotated[
        MatchSetRepositoryPort, Depends(get_match_set_repository)
    ],
) -> RegisterCardPort:
    return RegisterCardAdapter(
        match_repository,
        match_event_repository,
        team_repository,
        team_member_repository,
        user_repository,
        bracket_repository,
        modality_repository,
        modality_configuration_repository,
        volleyball_modality_configuration_repository,
        match_set_repository,
    )


def get_pause_clock_port(
    match_repository: Annotated[MatchRepositoryPort, Depends(get_match_repository)],
    match_event_repository: Annotated[
        MatchEventRepositoryPort, Depends(get_match_event_repository)
    ],
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    team_member_repository: Annotated[
        TeamMemberRepositoryPort, Depends(get_team_member_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    bracket_repository: Annotated[BracketRepositoryPort, Depends(get_bracket_repository)],
    modality_repository: Annotated[
        ModalityRepositoryPort, Depends(get_modality_repository)
    ],
    modality_configuration_repository: Annotated[
        ModalityConfigurationRepositoryPort,
        Depends(get_modality_configuration_repository),
    ],
    volleyball_modality_configuration_repository: Annotated[
        VolleyballModalityConfigurationRepositoryPort,
        Depends(get_volleyball_modality_configuration_repository),
    ],
    match_set_repository: Annotated[
        MatchSetRepositoryPort, Depends(get_match_set_repository)
    ],
) -> PauseClockPort:
    return PauseClockAdapter(
        match_repository,
        match_event_repository,
        team_repository,
        team_member_repository,
        user_repository,
        bracket_repository,
        modality_repository,
        modality_configuration_repository,
        volleyball_modality_configuration_repository,
        match_set_repository,
    )


def get_resume_clock_port(
    match_repository: Annotated[MatchRepositoryPort, Depends(get_match_repository)],
    match_event_repository: Annotated[
        MatchEventRepositoryPort, Depends(get_match_event_repository)
    ],
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    team_member_repository: Annotated[
        TeamMemberRepositoryPort, Depends(get_team_member_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    bracket_repository: Annotated[BracketRepositoryPort, Depends(get_bracket_repository)],
    modality_repository: Annotated[
        ModalityRepositoryPort, Depends(get_modality_repository)
    ],
    modality_configuration_repository: Annotated[
        ModalityConfigurationRepositoryPort,
        Depends(get_modality_configuration_repository),
    ],
    volleyball_modality_configuration_repository: Annotated[
        VolleyballModalityConfigurationRepositoryPort,
        Depends(get_volleyball_modality_configuration_repository),
    ],
    match_set_repository: Annotated[
        MatchSetRepositoryPort, Depends(get_match_set_repository)
    ],
) -> ResumeClockPort:
    return ResumeClockAdapter(
        match_repository,
        match_event_repository,
        team_repository,
        team_member_repository,
        user_repository,
        bracket_repository,
        modality_repository,
        modality_configuration_repository,
        volleyball_modality_configuration_repository,
        match_set_repository,
    )


def get_end_period_port(
    match_repository: Annotated[MatchRepositoryPort, Depends(get_match_repository)],
    match_event_repository: Annotated[
        MatchEventRepositoryPort, Depends(get_match_event_repository)
    ],
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    team_member_repository: Annotated[
        TeamMemberRepositoryPort, Depends(get_team_member_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    bracket_repository: Annotated[BracketRepositoryPort, Depends(get_bracket_repository)],
    modality_repository: Annotated[
        ModalityRepositoryPort, Depends(get_modality_repository)
    ],
    modality_configuration_repository: Annotated[
        ModalityConfigurationRepositoryPort,
        Depends(get_modality_configuration_repository),
    ],
    volleyball_modality_configuration_repository: Annotated[
        VolleyballModalityConfigurationRepositoryPort,
        Depends(get_volleyball_modality_configuration_repository),
    ],
    match_set_repository: Annotated[
        MatchSetRepositoryPort, Depends(get_match_set_repository)
    ],
) -> EndPeriodPort:
    return EndPeriodAdapter(
        match_repository,
        match_event_repository,
        team_repository,
        team_member_repository,
        user_repository,
        bracket_repository,
        modality_repository,
        modality_configuration_repository,
        volleyball_modality_configuration_repository,
        match_set_repository,
    )


def get_start_period_port(
    match_repository: Annotated[MatchRepositoryPort, Depends(get_match_repository)],
    match_event_repository: Annotated[
        MatchEventRepositoryPort, Depends(get_match_event_repository)
    ],
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    team_member_repository: Annotated[
        TeamMemberRepositoryPort, Depends(get_team_member_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    bracket_repository: Annotated[BracketRepositoryPort, Depends(get_bracket_repository)],
    modality_repository: Annotated[
        ModalityRepositoryPort, Depends(get_modality_repository)
    ],
    modality_configuration_repository: Annotated[
        ModalityConfigurationRepositoryPort,
        Depends(get_modality_configuration_repository),
    ],
    volleyball_modality_configuration_repository: Annotated[
        VolleyballModalityConfigurationRepositoryPort,
        Depends(get_volleyball_modality_configuration_repository),
    ],
    match_set_repository: Annotated[
        MatchSetRepositoryPort, Depends(get_match_set_repository)
    ],
) -> StartPeriodPort:
    return StartPeriodAdapter(
        match_repository,
        match_event_repository,
        team_repository,
        team_member_repository,
        user_repository,
        bracket_repository,
        modality_repository,
        modality_configuration_repository,
        volleyball_modality_configuration_repository,
        match_set_repository,
    )


def get_end_set_port(
    match_repository: Annotated[MatchRepositoryPort, Depends(get_match_repository)],
    match_event_repository: Annotated[
        MatchEventRepositoryPort, Depends(get_match_event_repository)
    ],
    team_repository: Annotated[TeamRepositoryPort, Depends(get_team_repository)],
    team_member_repository: Annotated[
        TeamMemberRepositoryPort, Depends(get_team_member_repository)
    ],
    user_repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    bracket_repository: Annotated[BracketRepositoryPort, Depends(get_bracket_repository)],
    modality_repository: Annotated[
        ModalityRepositoryPort, Depends(get_modality_repository)
    ],
    modality_configuration_repository: Annotated[
        ModalityConfigurationRepositoryPort,
        Depends(get_modality_configuration_repository),
    ],
    volleyball_modality_configuration_repository: Annotated[
        VolleyballModalityConfigurationRepositoryPort,
        Depends(get_volleyball_modality_configuration_repository),
    ],
    match_set_repository: Annotated[
        MatchSetRepositoryPort, Depends(get_match_set_repository)
    ],
) -> EndSetPort:
    return EndSetAdapter(
        match_repository,
        match_event_repository,
        team_repository,
        team_member_repository,
        user_repository,
        bracket_repository,
        modality_repository,
        modality_configuration_repository,
        volleyball_modality_configuration_repository,
        match_set_repository,
    )
