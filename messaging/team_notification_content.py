from typing import Optional, Tuple

DEFAULT_MEMBER_NAME = "Um integrante"


def _member_name(name: Optional[str]) -> str:
    cleaned = (name or "").strip()
    return cleaned or DEFAULT_MEMBER_NAME


def team_approved_content(team_name: str) -> Tuple[str, str]:
    return (
        "Seu time foi aprovado!",
        f"O time {team_name} foi aprovado para a temporada.",
    )


def team_rejected_content(team_name: str, reason: str) -> Tuple[str, str]:
    return (
        "Seu time foi rejeitado",
        f"O time {team_name} foi rejeitado. Motivo: {reason}",
    )


def member_removed_content(team_name: str) -> Tuple[str, str]:
    return (
        "Você foi removido do time",
        f"Você foi removido do time {team_name}.",
    )


def captain_selected_content(team_name: str) -> Tuple[str, str]:
    return (
        "Você é o novo capitão",
        f"Você foi escolhido capitão do time {team_name}.",
    )


def donation_confirmed_content(team_name: str) -> Tuple[str, str]:
    return (
        "Sua doação foi confirmada",
        f"Sua doação para o time {team_name} foi confirmada.",
    )


def member_joined_content(member_name: Optional[str], team_name: str) -> Tuple[str, str]:
    return (
        "Novo integrante no time",
        f"{_member_name(member_name)} entrou no seu time {team_name}.",
    )


def member_left_content(member_name: Optional[str], team_name: str) -> Tuple[str, str]:
    return (
        "Integrante saiu do time",
        f"{_member_name(member_name)} saiu do seu time {team_name}.",
    )
