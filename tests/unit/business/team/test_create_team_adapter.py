from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from business.team.create_team_adapter import CreateTeamAdapter
from core.context import Context
from domain.enums.gender import Gender
from domain.enums.modality_gender_mode import ModalityGenderMode
from domain.enums.season_status import SeasonStatus
from domain.exceptions.business_exception import BusinessException
from domain.modality.modality import Modality
from domain.season.season import Season
from domain.team.team import Team
from domain.user.user import User


def make_adapter():
    team_repository = AsyncMock()
    team_member_repository = AsyncMock()
    user_repository = AsyncMock()
    season_repository = AsyncMock()
    season_modality_repository = AsyncMock()
    modality_repository = AsyncMock()
    audit_logger = AsyncMock()
    file_storage = AsyncMock()
    file_storage.upload.side_effect = lambda **kw: kw["object_key"]

    adapter = CreateTeamAdapter(
        team_repository,
        team_member_repository,
        user_repository,
        season_repository,
        season_modality_repository,
        modality_repository,
        audit_logger,
        file_storage,
    )
    return (
        adapter,
        team_repository,
        team_member_repository,
        user_repository,
        season_repository,
        season_modality_repository,
        modality_repository,
        audit_logger
    )


def make_open_season(season_id=None):
    return Season(
        id=season_id or uuid4(),
        name="Intercurso 2026",
        status=SeasonStatus.REGISTRATION_OPEN,
        registration_start_date=datetime.now(timezone.utc) - timedelta(days=1),
        registration_end_date=datetime.now(timezone.utc) + timedelta(days=5),
    )


def make_context(name="Time A", modality_id=None, creator_user_id=None):
    team = Team(name=name, modality_id=modality_id or uuid4())
    context = Context(data=team)
    context.put_property(
        "creator_user_id", creator_user_id if creator_user_id is not None else uuid4()
    )
    return context, team


@pytest.mark.unit
class TestCreateTeamAdapter:
    async def test_creates_team_with_owner_member(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
            audit_logger
        ) = make_adapter()

        active_season = make_open_season()
        creator_user_id = uuid4()

        context, team = make_context(creator_user_id=creator_user_id)

        season_repository.find_active_season.return_value = active_season
        modality_repository.exists_by_id.return_value = True
        season_modality_repository.exists_by_season_and_modality.return_value = True
        team_repository.exists_by_user_season_and_modality.return_value = False

        saved_team = Team(
            id=uuid4(),
            name=team.name,
            modality_id=team.modality_id,
            season_id=active_season.id,
            owner_id=creator_user_id,
        )
        team_repository.save.return_value = saved_team
        user_repository.get.return_value = User(id=creator_user_id, atleta=False)

        result = await adapter.execute(context)

        assert result.id == saved_team.id
        team_repository.save.assert_awaited_once()
        team_member_repository.save.assert_awaited_once()
        user_repository.save.assert_awaited_once()

        owner_member = context.get_property("owner_member", object)
        assert owner_member is not None

    async def test_blocks_when_creator_gender_does_not_match_modality(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
            audit_logger,
        ) = make_adapter()

        active_season = make_open_season()
        creator_user_id = uuid4()
        context, team = make_context(creator_user_id=creator_user_id)

        season_repository.find_active_season.return_value = active_season
        modality_repository.get.return_value = Modality(
            id=team.modality_id,
            name="Futsal Feminino",
            min_members=5,
            max_members=10,
            gender_mode=ModalityGenderMode.FEMALE,
        )
        season_modality_repository.exists_by_season_and_modality.return_value = True
        user_repository.get.return_value = User(
            id=creator_user_id, gender=Gender.MALE
        )

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        team_repository.save.assert_not_awaited()

    async def test_allows_when_creator_gender_matches_modality(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
            audit_logger,
        ) = make_adapter()

        active_season = make_open_season()
        creator_user_id = uuid4()
        context, team = make_context(creator_user_id=creator_user_id)

        season_repository.find_active_season.return_value = active_season
        modality_repository.get.return_value = Modality(
            id=team.modality_id,
            name="Futsal Masculino",
            min_members=5,
            max_members=10,
            gender_mode=ModalityGenderMode.MALE,
        )
        season_modality_repository.exists_by_season_and_modality.return_value = True
        team_repository.exists_by_user_season_and_modality.return_value = False
        user_repository.get.return_value = User(
            id=creator_user_id, gender=Gender.MALE, atleta=False
        )
        team_repository.save.return_value = Team(
            id=uuid4(),
            name=team.name,
            modality_id=team.modality_id,
            season_id=active_season.id,
            owner_id=creator_user_id,
        )

        result = await adapter.execute(context)

        assert result is not None
        team_repository.save.assert_awaited_once()

    async def test_allows_mixed_modality_regardless_of_creator_gender(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
            audit_logger,
        ) = make_adapter()

        active_season = make_open_season()
        creator_user_id = uuid4()
        context, team = make_context(creator_user_id=creator_user_id)

        season_repository.find_active_season.return_value = active_season
        modality_repository.get.return_value = Modality(
            id=team.modality_id,
            name="Voleibol",
            min_members=6,
            max_members=12,
            gender_mode=ModalityGenderMode.MIXED,
            min_male_members=2,
            min_female_members=2,
        )
        season_modality_repository.exists_by_season_and_modality.return_value = True
        team_repository.exists_by_user_season_and_modality.return_value = False
        user_repository.get.return_value = User(
            id=creator_user_id, gender=Gender.FEMALE, atleta=False
        )
        team_repository.save.return_value = Team(
            id=uuid4(),
            name=team.name,
            modality_id=team.modality_id,
            season_id=active_season.id,
            owner_id=creator_user_id,
        )

        result = await adapter.execute(context)

        assert result is not None
        team_repository.save.assert_awaited_once()

    async def test_blocks_when_no_active_season(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
            audit_logger
        ) = make_adapter()

        context, _ = make_context()
        season_repository.find_active_season.return_value = None

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        team_repository.save.assert_not_awaited()

    async def test_blocks_when_season_not_registration_open(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
            audit_logger
        ) = make_adapter()

        context, _ = make_context()
        season = make_open_season()
        season.status = SeasonStatus.REGISTRATION_CLOSED
        season_repository.find_active_season.return_value = season

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_registration_period_not_started(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
            audit_logger
        ) = make_adapter()

        context, _ = make_context()
        season = make_open_season()
        season.registration_start_date = datetime.now(timezone.utc) + timedelta(days=1)
        season_repository.find_active_season.return_value = season

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_registration_period_ended(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
            audit_logger
        ) = make_adapter()

        context, _ = make_context()
        season = make_open_season()
        season.registration_end_date = datetime.now(timezone.utc) - timedelta(days=1)
        season_repository.find_active_season.return_value = season

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_modality_does_not_exist(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
            audit_logger
        ) = make_adapter()

        context, _ = make_context()
        season_repository.find_active_season.return_value = make_open_season()
        modality_repository.exists_by_id.return_value = False

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_modality_not_in_active_season(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
            audit_logger,
        ) = make_adapter()

        context, _ = make_context()
        season_repository.find_active_season.return_value = make_open_season()
        modality_repository.exists_by_id.return_value = True
        season_modality_repository.exists_by_season_and_modality.return_value = False

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_user_already_has_team_in_modality(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
            audit_logger
        ) = make_adapter()

        active_season = make_open_season()
        creator_user_id = uuid4()
        context, team = make_context(creator_user_id=creator_user_id)

        season_repository.find_active_season.return_value = active_season
        modality_repository.exists_by_id.return_value = True
        season_modality_repository.exists_by_season_and_modality.return_value = True

        team_repository.exists_by_user_season_and_modality.return_value = True

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        team_repository.save.assert_not_awaited()

    async def test_blocks_when_team_data_is_missing(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
            audit_logger
        ) = make_adapter()

        context = Context()
        context.put_property("creator_user_id", uuid4())

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_blocks_when_creator_user_id_is_missing(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
            audit_logger
        ) = make_adapter()

        team = Team(name="Time A", modality_id=uuid4())
        context = Context(data=team)

        with pytest.raises(BusinessException):
            await adapter.execute(context)

    async def test_marks_creator_as_atleta_when_not_already(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
            audit_logger
        ) = make_adapter()

        active_season = make_open_season()
        creator_user_id = uuid4()
        context, team = make_context(creator_user_id=creator_user_id)

        season_repository.find_active_season.return_value = active_season
        modality_repository.exists_by_id.return_value = True
        season_modality_repository.exists_by_season_and_modality.return_value = True
        team_repository.exists_by_user_season_and_modality.return_value = False
        team_repository.save.return_value = Team(id=uuid4(), name=team.name)

        creator_user = User(id=creator_user_id, atleta=False)
        user_repository.get.return_value = creator_user

        await adapter.execute(context)

        assert creator_user.atleta is True
        user_repository.save.assert_awaited_once_with(creator_user)

    async def test_does_not_resave_user_already_atleta(self):
        (
            adapter,
            team_repository,
            team_member_repository,
            user_repository,
            season_repository,
            season_modality_repository,
            modality_repository,
            audit_logger
        ) = make_adapter()

        active_season = make_open_season()
        creator_user_id = uuid4()
        context, team = make_context(creator_user_id=creator_user_id)

        season_repository.find_active_season.return_value = active_season
        modality_repository.exists_by_id.return_value = True
        season_modality_repository.exists_by_season_and_modality.return_value = True
        team_repository.exists_by_user_season_and_modality.return_value = False
        team_repository.save.return_value = Team(id=uuid4(), name=team.name)

        user_repository.get.return_value = User(id=creator_user_id, atleta=True)

        await adapter.execute(context)

        user_repository.save.assert_not_awaited()


PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32
JPG = b"\xff\xd8\xff\xe0" + b"0" * 32
WEBP = b"RIFF\x00\x00\x00\x00WEBP" + b"0" * 32


def arrange_valid_flow(parts, photo_bytes):
    adapter, team_repo, member_repo, user_repo, season_repo, season_mod_repo, mod_repo, _ = parts
    season = make_open_season()
    season_repo.find_active_season.return_value = season
    mod_repo.get.return_value = Modality(id=uuid4(), name="Futsal", gender_mode=ModalityGenderMode.MIXED)
    season_mod_repo.exists_by_season_and_modality.return_value = True
    team_repo.exists_by_user_season_and_modality.return_value = False
    team_repo.save.side_effect = lambda t: t
    member_repo.save.side_effect = lambda m: m
    user_repo.get.return_value = User(id=uuid4(), name="X", atleta=True)
    context, _ = make_context()
    if photo_bytes is not None:
        context.put_property("photo_bytes", photo_bytes)
    return adapter, team_repo, member_repo, context


@pytest.mark.unit
class TestCreateTeamPhoto:
    @pytest.mark.parametrize(
        "data,ext,ctype",
        [(PNG, "png", "image/png"), (JPG, "jpg", "image/jpeg"), (WEBP, "webp", "image/webp")],
    )
    async def test_uploads_photo_and_stores_object_key(self, data, ext, ctype):
        adapter, team_repo, _, context = arrange_valid_flow(make_adapter(), data)

        team = await adapter.execute(context)

        kwargs = adapter.file_storage.upload.await_args.kwargs
        assert kwargs["object_key"].startswith("teams/") and kwargs["object_key"].endswith(f".{ext}")
        assert kwargs["content_type"] == ctype and kwargs["file_bytes"] == data
        assert team.photo == kwargs["object_key"]

    async def test_no_photo_means_no_upload(self):
        adapter, _, _, context = arrange_valid_flow(make_adapter(), None)

        team = await adapter.execute(context)

        adapter.file_storage.upload.assert_not_awaited()
        assert team.photo is None

    async def test_rejects_non_image_content_before_any_io(self):
        parts = make_adapter()
        adapter, team_repo, _, context = arrange_valid_flow(parts, b"%PDF-1.4 not an image")

        with pytest.raises(BusinessException, match="Formato de imagem inválido"):
            await adapter.execute(context)

        adapter.file_storage.upload.assert_not_awaited()
        team_repo.save.assert_not_awaited()

    async def test_rejects_oversized_photo(self):
        adapter, _, _, context = arrange_valid_flow(make_adapter(), PNG + b"0" * (5 * 1024 * 1024))

        with pytest.raises(BusinessException, match="5MB"):
            await adapter.execute(context)

        adapter.file_storage.upload.assert_not_awaited()

    async def test_business_rejection_does_not_upload(self):
        parts = make_adapter()
        adapter, team_repo, _, context = arrange_valid_flow(parts, PNG)
        team_repo.exists_by_user_season_and_modality.return_value = True  # já tem time

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        adapter.file_storage.upload.assert_not_awaited()

    async def test_deletes_uploaded_photo_when_save_fails(self):
        adapter, team_repo, _, context = arrange_valid_flow(make_adapter(), PNG)
        team_repo.save.side_effect = RuntimeError("db down")

        with pytest.raises(RuntimeError):
            await adapter.execute(context)

        key = adapter.file_storage.upload.await_args.kwargs["object_key"]
        adapter.file_storage.delete.assert_awaited_once_with(key)
