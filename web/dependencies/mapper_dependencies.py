from typing import Annotated

from fastapi import Depends

from core.storage.file_storage_port import FileStoragePort
from web.dependencies.business.storage_dependencies import get_file_storage
from web.mappers.modality_model_mapper import ModalityModelMapper
from web.mappers.season_model_mapper import SeasonModelMapper
from web.mappers.team_model_mapper import TeamModelMapper
from web.mappers.user_model_mapper import UserModelMapper
from web.mappers.bracket_model_mapper import BracketModelMapper
from web.mappers.match_model_mapper import MatchModelMapper


def get_user_model_mapper() -> UserModelMapper:
    return UserModelMapper()


def get_modality_model_mapper() -> ModalityModelMapper:
    return ModalityModelMapper()


def get_team_model_mapper(
    file_storage: Annotated[FileStoragePort, Depends(get_file_storage)],
) -> TeamModelMapper:
    return TeamModelMapper(file_storage)


def get_season_model_mapper() -> SeasonModelMapper:
    return SeasonModelMapper()


def get_bracket_model_mapper() -> BracketModelMapper:
    return BracketModelMapper()


def get_match_model_mapper() -> MatchModelMapper:
    return MatchModelMapper()
