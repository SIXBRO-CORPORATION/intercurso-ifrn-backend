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
    require_role,
    require_monitor,
    require_admin,
)

from web.dependencies.business.user_dependencies import (
    create_user_port,
    get_user_profile_port,
    get_create_user_by_admin_port,
    get_update_user_by_admin_port,
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
    get_manage_season_port,
    get_close_registration_port,
    get_reopen_registration_port,
    get_season_details_port,
)

from web.dependencies.mapper_dependencies import (
    get_user_model_mapper,
    get_modality_model_mapper,
    get_team_model_mapper,
    get_season_model_mapper,
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
    "require_role",
    "require_monitor",
    "require_admin",

    # Business Dependencies - Users
    "create_user_port",
    "get_user_profile_port",
    "get_create_user_by_admin_port",
    "get_update_user_by_admin_port",

    # Business Dependencies - Teams
    "get_create_team_port",
    "get_approve_team_port",
    "get_confirm_donation_team_port",

    # Business Dependencies - Modalities
    "get_create_modality_port",

    # Business Dependencies - Seasons
    "get_create_season_port",
    "get_manage_season_port",
    "get_close_registration_port",
    "get_reopen_registration_port",
    "get_season_details_port",

    # Mapper Dependencies
    "get_user_model_mapper",
    "get_modality_model_mapper",
    "get_team_model_mapper",
    "get_season_model_mapper",
]