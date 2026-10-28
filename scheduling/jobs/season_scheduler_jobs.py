import logging
from datetime import datetime, timezone
from typing import List, Optional

from core.messaging.season_broadcast_port import SeasonBroadcastPort
from domain.enums.season_status import SeasonStatus
from domain.season.season import Season
from messaging.adapters.fcm_push_sender_adapter import FCMPushSenderAdapter
from messaging.services.season_broadcast_notifier import SeasonBroadcastNotifier
from persistence.adapters.season.season_repository_adapter import SeasonRepositoryAdapter
from persistence.database import AsyncSessionLocal
from persistence.mappers.season.season_mapper import SeasonMapper

logger = logging.getLogger(__name__)


def _build_season_broadcast() -> Optional[SeasonBroadcastPort]:
    try:
        return SeasonBroadcastNotifier(push_sender=FCMPushSenderAdapter())
    except Exception:
        logger.exception(
            "Não foi possível inicializar o envio de notificações de temporada"
        )
        return None


async def _notify_after_commit(
    notify,
    seasons: List[Season],
) -> None:
    if not seasons:
        return

    season_broadcast = _build_season_broadcast()
    if season_broadcast is None:
        return

    for season in seasons:
        try:
            await notify(season_broadcast, season)
        except Exception:
            logger.exception(
                "Falha ao disparar notificação da temporada %s", season.id
            )


async def run_open_seasons_job() -> None:

    async with AsyncSessionLocal() as session:
        opened_seasons: List[Season] = []
        try:
            repository = SeasonRepositoryAdapter(session, SeasonMapper())
            now = datetime.now(timezone.utc)

            seasons_to_open = await repository.find_draft_ready_to_open(now)
            for season in seasons_to_open:

                currently_active = await repository.find_active_season()
                if currently_active is not None:
                    logger.warning(
                        "Abertura automática da temporada %s adiada: a temporada %s ainda está ativa",
                        season.id,
                        currently_active.id,
                    )
                    continue

                season.status = SeasonStatus.REGISTRATION_OPEN
                season.active = True
                season.registration_opened_at = now
                await repository.save(season)
                opened_seasons.append(season)

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
            return

    await _notify_after_commit(
        lambda broadcast, season: broadcast.registration_opened(season),
        opened_seasons,
    )


async def run_close_seasons_job() -> None:

    async with AsyncSessionLocal() as session:
        closed_seasons: List[Season] = []
        try:
            repository = SeasonRepositoryAdapter(session, SeasonMapper())
            now = datetime.now(timezone.utc)

            seasons_to_close = await repository.find_open_with_registration_ended(now)
            for season in seasons_to_close:
                season.status = SeasonStatus.REGISTRATION_CLOSED
                season.registration_closed_at = now
                await repository.save(season)
                closed_seasons.append(season)

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
            return

    await _notify_after_commit(
        lambda broadcast, season: broadcast.registration_closed(season),
        closed_seasons,
    )
