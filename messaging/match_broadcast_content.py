from typing import Optional, Sequence, Tuple

from domain.enums.card_type import CardType

BROADCAST_TOPIC = "live_matches"


def broadcast_push_content(
    event_types: Sequence[str],
    team1_name: str,
    team2_name: str,
    team1_score: int,
    team2_score: int,
    card_type: Optional[CardType] = None,
) -> Optional[Tuple[str, str]]:
    
    score = f"{team1_score} x {team2_score}"

    if "match_started" in event_types:
        return ("Partida começou!", f"{team1_name} x {team2_name} já está rolando.")

    if "goal_scored" in event_types:
        return ("Gol!", f"{team1_name} {score} {team2_name}")

    if "card_issued" in event_types and card_type == CardType.RED:
        return ("Cartão vermelho!", f"{team1_name} x {team2_name}")

    if "match_finished" in event_types:
        return ("Partida encerrada", f"{team1_name} {score} {team2_name}")

    return None
