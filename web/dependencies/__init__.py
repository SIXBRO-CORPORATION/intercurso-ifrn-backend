from web.dependencies.persistence_dependencies import (
    get_user_repository,
    get_team_repository,
    get_team_member_repository,
)

from web.dependencies.security_dependencies import (
    get_jwt_provider,
    get_current_user_id,
    get_current_user,
    get_optional_current_user,
    require_authenticated_user,
)

from web.dependencies.business.user_dependencies import (
    create_user_port,
    get_user_profile_port,
)

from web.dependencies.business.team_dependencies import (
    get_create_team_port,
    get_approve_team_port,
    get_confirm_donation_team_port,
)

from web.dependencies.business.modality_dependencies import (
    get_create_modality_port,
)

from web.dependencies.business.season_dependencies import (
    get_create_season_port,
)

__all__ = [
    # Persistence Dependencies
    "get_user_repository",
    "get_team_repository",
    "get_team_member_repository",

    # Security Dependencies
    "get_jwt_provider",
    "get_current_user_id",
    "get_current_user",
    "get_optional_current_user",
    "require_authenticated_user",

    # Business Dependencies - Users
    "create_user_port",
    "get_user_profile_port",

    # Business Dependencies - Teams
    "get_create_team_port",
    "get_approve_team_port",
    "get_confirm_donation_team_port",

    # Business Dependencies - Modalities
    "get_create_modality_port",

    # Business Dependencies - Seasons
    "get_create_season_port",
]