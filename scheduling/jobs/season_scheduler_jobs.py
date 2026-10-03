import logging
from datetime import datetime, timezone

from domain.enums.season_status import SeasonStatus
from persistence.adapters.season.season_repository_adapter import SeasonRepositoryAdapter
from persistence.database import AsyncSessionLocal
from persistence.mappers.season.season_mapper import SeasonMapper

logger = logging.getLogger(__name__)


async def run_open_seasons_job() -> None:

    async with AsyncSessionLocal() as session:
        try:
            repository = SeasonRepositoryAdapter(session, SeasonMapper())
            now = datetime.now(timezone.utc)

            seasons_to_open = await repository.find_draft_ready_to_open(now)
            for season in seasons_to_open:
                currently_active = await repository.find_active_season()
                if currently_active is not None and currently_active.id != season.id:
                    currently_active.active = False
                    await repository.save(currently_active)

                season.status = SeasonStatus.REGISTRATION_OPEN
                season.active = True
                season.registration_opened_at = now
                await repository.save(season)

                logger.info(
                    "Temporada %s aberta automaticamente (Sistema Automático)",
                    season.id,
                )

            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception(
                "Falha ao executar job de abertura automática de temporadas"
            )


async def run_close_seasons_job() -> None:

    async with AsyncSessionLocal() as session:
        try:
            repository = SeasonRepositoryAdapter(session, SeasonMapper())
            now = datetime.now(timezone.utc)

            seasons_to_close = await repository.find_open_with_registration_ended(now)
            for season in seasons_to_close:
                season.status = SeasonStatus.REGISTRATION_CLOSED
                season.registration_closed_at = now
                await repository.save(season)

                logger.info(
                    "Temporada %s encerrada automaticamente (Sistema Automático)",
                    season.id,
                )

            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception(
                "Falha ao executar job de encerramento automático de temporadas"
            )
