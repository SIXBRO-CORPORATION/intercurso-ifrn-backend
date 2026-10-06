import secrets
import uuid
from contextlib import suppress
from datetime import datetime, timezone
from uuid import UUID

from core.business.audit.audit_logger import AuditLogger
from core.business.team.create_team_port import CreateTeamPort
from core.context import Context
from core.persistence.modality.modality_repository_port import ModalityRepositoryPort
from core.persistence.season.season_modality_repository_port import (
    SeasonModalityRepositoryPort,
)
from core.persistence.season.season_repository_port import SeasonRepositoryPort
from core.persistence.team.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from core.storage.file_storage_port import FileStoragePort
from domain.enums.audit_action import AuditAction
from domain.enums.modality_gender_mode import ModalityGenderMode
from domain.enums.season_status import SeasonStatus
from domain.enums.team_member_role import TeamMemberRole
from domain.enums.donation_status import DonationStatus
from domain.exceptions.business_exception import BusinessException
from domain.team.team import Team
from domain.team.team_photo import (
    MAX_TEAM_PHOTO_BYTES,
    TEAM_PHOTO_FOLDER,
    sniff_team_photo,
)
from domain.team.team_member import TeamMember


class CreateTeamAdapter(CreateTeamPort):
    def __init__(
        self,
        team_repository: TeamRepositoryPort,
        team_member_repository: TeamMemberRepositoryPort,
        user_repository: UserRepositoryPort,
        season_repository: SeasonRepositoryPort,
        season_modality_repository: SeasonModalityRepositoryPort,
        modality_repository: ModalityRepositoryPort,
        audit_logger: AuditLogger,
        file_storage: FileStoragePort,
    ):
        self.team_repository = team_repository
        self.team_member_repository = team_member_repository
        self.user_repository = user_repository
        self.season_repository = season_repository
        self.season_modality_repository = season_modality_repository
        self.modality_repository = modality_repository
        self.audit_logger = audit_logger
        self.file_storage = file_storage

    async def execute(self, context: Context) -> Team:
        team = context.get_data(Team)
        creator_user_id = context.get_property("creator_user_id", UUID)

        if team is None:
            raise BusinessException("Dados do time são obrigatórios")

        if creator_user_id is None:
            raise BusinessException("Usuário criador é obrigatório")

        if team.modality_id is None:
            raise BusinessException("Modalidade é obrigatória")

        photo_bytes = context.get_property("photo_bytes", bytes)
        photo_type = None
        if photo_bytes:
            if len(photo_bytes) > MAX_TEAM_PHOTO_BYTES:
                raise BusinessException(
                    "Arquivo de foto excede o tamanho máximo permitido de 5MB"
                )
            photo_type = sniff_team_photo(photo_bytes)
            if photo_type is None:
                raise BusinessException(
                    "Formato de imagem inválido. Envie um arquivo PNG, JPG ou WEBP"
                )

        active_season = await self.season_repository.find_active_season()

        if active_season is None or active_season.status != SeasonStatus.REGISTRATION_OPEN:
            raise BusinessException(
                "Não há uma temporada com inscrições abertas no momento"
            )

        now = datetime.now(timezone.utc)
        if active_season.registration_start_date and now < active_season.registration_start_date:
            raise BusinessException("O período de inscrição ainda não foi iniciado")
        if active_season.registration_end_date and now > active_season.registration_end_date:
            raise BusinessException("O período de inscrição já foi encerrado")

        modality = await self.modality_repository.get(team.modality_id)
        if modality is None:
            raise BusinessException("Modalidade informada não existe")

        modality_in_season = await self.season_modality_repository.exists_by_season_and_modality(
            active_season.id, team.modality_id
        )
        if not modality_in_season:
            raise BusinessException(
                "Modalidade informada não faz parte da temporada ativa"
            )

        creator_user = await self.user_repository.get(creator_user_id)

        if modality.gender_mode in (ModalityGenderMode.MALE, ModalityGenderMode.FEMALE):
            if creator_user is None or creator_user.gender is None:
                raise BusinessException(
                    "Não foi possível confirmar seu gênero junto ao SUAP para "
                    "validar a inscrição nesta modalidade"
                )
            if creator_user.gender.name != modality.gender_mode.name:
                raise BusinessException(
                    f"Esta modalidade é exclusiva para o gênero "
                    f"{modality.gender_mode.value}"
                )

        already_in_modality = await self.team_repository.exists_by_user_season_and_modality(
            creator_user_id, active_season.id, team.modality_id
        )

        if already_in_modality:
            raise BusinessException(
                "Você já participa de um time nessa modalidade na temporada ativa"
            )

        # Upload só depois de todas as validações de negócio: não sobra objeto
        # órfão no bucket quando o cadastro é recusado.
        photo_key = None
        if photo_type is not None:
            content_type, ext = photo_type
            photo_key = f"{TEAM_PHOTO_FOLDER}/{uuid.uuid4()}.{ext}"
            await self.file_storage.upload(
                file_bytes=photo_bytes, object_key=photo_key, content_type=content_type
            )

        try:
            new_team = Team(
                name=team.name,
                photo=photo_key,
                season_id=active_season.id,
                modality_id=team.modality_id,
                owner_id=creator_user_id,
                invite_token=secrets.token_urlsafe(16),
                token_active=True,
            )

            saved_team = await self.team_repository.save(new_team)

            owner_member = TeamMember(
                team_id=saved_team.id,
                user_id=creator_user_id,
                role=TeamMemberRole.OWNER,
                donation_status=DonationStatus.PENDING_DONATION,
                joined_at=now,
            )
            saved_owner_member = await self.team_member_repository.save(owner_member)
        except Exception:
            # ponytail: o commit acontece em get_db(), depois do handler; falha de
            # commit ainda deixa o objeto órfão. Se incomodar, job de sweep no bucket.
            if photo_key is not None:
                with suppress(Exception):  # best-effort: o erro original é o que importa
                    await self.file_storage.delete(photo_key)
            raise

        if creator_user is not None and not creator_user.atleta:
            creator_user.atleta = True
            await self.user_repository.save(creator_user)

        context.put_property("owner_member", saved_owner_member)
        context.put_property("team_members", [saved_owner_member])

        await self.audit_logger.log(
            action=AuditAction.TEAM_CREATED,
            description=(
                f"Time '{saved_team.name}' criado na temporada "
                f"'{active_season.name}'"
            ),
            actor_id=creator_user_id,
            actor=creator_user,
        )

        return saved_team
