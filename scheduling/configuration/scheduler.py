import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from scheduling.jobs.season_scheduler_jobs import (
    run_close_seasons_job,
    run_open_seasons_job,
)

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler() -> None:

    scheduler.add_job(
        run_open_seasons_job,
        trigger=CronTrigger(hour=0, minute=0),
        id="open_seasons_job",
        name="Abertura automática de inscrições de temporadas",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    scheduler.add_job(
        run_close_seasons_job,
        trigger=CronTrigger(hour=0, minute=0),
        id="close_seasons_job",
        name="Encerramento automático de inscrições de temporadas",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )

    scheduler.start()
    logger.info("Scheduler de temporadas iniciado (verificação a cada 1 dia)")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler de temporadas finalizado")
