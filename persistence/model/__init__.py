from persistence.model.user.user_entity import UserEntity
from persistence.model.team.team_entity import TeamEntity
from persistence.model.team.team_member_entity import TeamMemberEntity
from persistence.model.season.season_entity import SeasonEntity
from persistence.model.season.season_modality_entity import SeasonModalityEntity
from persistence.model.auth.refresh_token_entity import RefreshTokenEntity
from persistence.model.modality.modality_entity import ModalityEntity
from persistence.model.modality.modality_configuration_entity import ModalityConfigurationEntity
from persistence.model.match.match_entity import MatchEntity
from persistence.model.match.match_event_entity import MatchEventEntity
from persistence.model.bracket.bracket_entity import BracketEntity
from persistence.model.bracket.bracket_group_entity import BracketGroupEntity
from persistence.model.bracket.bracket_group_team_entity import BracketGroupTeamEntity
from persistence.model.modality.volleybal. volleyball_modality_configuration_entity import VolleyballModalityConfigurationEntity
from persistence.model.match.match_set_entity import MatchSetEntity, PG_ENTITIES as MATCH_SET_PG_ENTITIES


PG_ENTITIES = [
    *MATCH_SET_PG_ENTITIES,
]

__all__ = [
    "UserEntity",
    "TeamEntity",
    "TeamMemberEntity",
    "SeasonEntity",
    "SeasonModalityEntity",
    "RefreshTokenEntity",
    "ModalityEntity",
    "ModalityConfigurationEntity",
    "VolleyballModalityConfigurationEntity",
    "MatchEntity",
    "MatchEventEntity",
    "MatchSetEntity",
    "BracketEntity",
    "BracketGroupEntity",
    "BracketGroupTeamEntity",
]