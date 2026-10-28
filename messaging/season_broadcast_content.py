from datetime import datetime
from typing import Optional, Tuple
from zoneinfo import ZoneInfo

SEASON_TOPIC = "season_updates"

_LOCAL_TIMEZONE = ZoneInfo("America/Fortaleza")


def _format_date(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    if value.tzinfo is not None:
        value = value.astimezone(_LOCAL_TIMEZONE)
    return value.strftime("%d/%m/%Y às %H:%M")


def registration_opened_content(
    season_name: str, registration_end_date: Optional[datetime]
) -> Tuple[str, str]:
    body = f"As inscrições para a temporada {season_name} já estão abertas."
    end = _format_date(registration_end_date)
    if end:
        body = f"As inscrições para a temporada {season_name} estão abertas até {end}."
    return ("Inscrições abertas!", body)


def registration_closed_content(season_name: str) -> Tuple[str, str]:
    return (
        "Inscrições encerradas",
        f"As inscrições para a temporada {season_name} foram encerradas.",
    )


def registration_reopened_content(
    season_name: str, registration_end_date: Optional[datetime]
) -> Tuple[str, str]:
    body = f"As inscrições para a temporada {season_name} foram reabertas."
    end = _format_date(registration_end_date)
    if end:
        body = (
            f"As inscrições para a temporada {season_name} foram reabertas "
            f"até {end}."
        )
    return ("Inscrições reabertas!", body)


def season_finished_content(season_name: str) -> Tuple[str, str]:
    return (
        "Temporada encerrada",
        f"A temporada {season_name} foi encerrada. Confira os resultados!",
    )
