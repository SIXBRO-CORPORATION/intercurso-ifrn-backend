from web.mappers.modality_model_mapper import ModalityModelMapper
from web.mappers.season_model_mapper import SeasonModelMapper
from web.mappers.team_model_mapper import TeamModelMapper
from web.mappers.user_model_mapper import UserModelMapper
from web.mappers.bracket_model_mapper import BracketModelMapper


def get_user_model_mapper() -> UserModelMapper:
    return UserModelMapper()


def get_modality_model_mapper() -> ModalityModelMapper:
    return ModalityModelMapper()


def get_team_model_mapper() -> TeamModelMapper:
    return TeamModelMapper()


def get_season_model_mapper() -> SeasonModelMapper:
    return SeasonModelMapper()


def get_bracket_model_mapper() -> BracketModelMapper:
    return BracketModelMapper()
