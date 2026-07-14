from domain.enums.modality_format import ModalityFormat
from domain.exceptions.business_exception import BusinessException

DEFAULT_CLASSIFIED_PER_GROUP = 2


def validate_team_count_for_format(modality_format: ModalityFormat, team_count: int) -> None:
    """Valida se a quantidade de times aprovados é compatível com o formato escolhido.

    Regra de negócio combinada com o time: TRIANGULAR só pode ser usado quando a
    modalidade tem exatamente 3 times aprovados (não é uma variação de grupos de 3).
    """
    if team_count < 2:
        raise BusinessException(
            "É necessário ao menos 2 times aprovados para criar um chaveamento"
        )

    if modality_format == ModalityFormat.TRIANGULAR and team_count != 3:
        raise BusinessException(
            "O formato Triangular só pode ser utilizado quando a modalidade tiver "
            "exatamente 3 times aprovados"
        )


def _distribute_evenly(total: int, parts: int) -> list[int]:
    base = total // parts
    remainder = total % parts
    return [base + (1 if i < remainder else 0) for i in range(parts)]


def _suggest_group_stage_knockout(team_count: int) -> dict:
    """Escolhe nº de grupos (sempre potência de 2) de forma que o total de
    classificados (nº de grupos x classificados por grupo) também seja potência
    de 2 — assim a fase de mata-mata nunca precisa de BYE. Tenta manter grupos
    com ao menos 3 times sempre que possível."""
    classified_per_group = DEFAULT_CLASSIFIED_PER_GROUP

    max_groups_with_min_size = max(team_count // 3, 1)

    num_groups = 1
    candidate = 2
    while (
        candidate <= max_groups_with_min_size
        and candidate * classified_per_group <= team_count
    ):
        num_groups = candidate
        candidate *= 2

    if num_groups < 2 and team_count >= 4:
        num_groups = 2

    group_sizes = _distribute_evenly(team_count, num_groups)

    return {
        "num_groups": num_groups,
        "classified_per_group": classified_per_group,
        "group_sizes": group_sizes,
    }


def suggest_configuration(modality_format: ModalityFormat, team_count: int) -> dict:
    """Gera a configuração sugerida (UC011, fluxo principal passo 7) para o
    formato escolhido, sem persistir nada."""
    if modality_format == ModalityFormat.KNOCKOUT:
        return {}

    if modality_format == ModalityFormat.GROUP_STAGE_KNOCKOUT:
        return _suggest_group_stage_knockout(team_count)

    if modality_format == ModalityFormat.ROUND_ROBIN:
        return {"rounds": 1}

    if modality_format == ModalityFormat.TRIANGULAR:
        return {"double_round": False}

    raise BusinessException("Formato de chaveamento não suportado")


def resolve_configuration(
    modality_format: ModalityFormat, team_count: int, configuration: dict | None
) -> dict:
    """Mescla a configuração informada pelo monitor (Fluxo Alternativo 3 - ajustar
    configuração) com os defaults sugeridos, e valida consistência."""
    suggested = suggest_configuration(modality_format, team_count)
    resolved = {**suggested, **(configuration or {})}

    if modality_format == ModalityFormat.GROUP_STAGE_KNOCKOUT:
        num_groups = resolved.get("num_groups")
        classified_per_group = resolved.get("classified_per_group")

        if not isinstance(num_groups, int) or num_groups < 1:
            raise BusinessException("Número de grupos inválido")
        if not isinstance(classified_per_group, int) or classified_per_group < 1:
            raise BusinessException("Número de classificados por grupo inválido")
        if num_groups > team_count:
            raise BusinessException(
                "Número de grupos não pode ser maior que o número de times aprovados"
            )

        total_classified = num_groups * classified_per_group
        if total_classified < 2 or (total_classified & (total_classified - 1)) != 0:
            raise BusinessException(
                "O total de classificados (grupos x classificados por grupo) precisa "
                "ser uma potência de 2 (2, 4, 8, 16...) para montar a fase de mata-mata"
            )
        if classified_per_group > min(_distribute_evenly(team_count, num_groups)):
            raise BusinessException(
                "Número de classificados por grupo maior que a quantidade de times "
                "do menor grupo"
            )

        # regenera os tamanhos de grupo caso o monitor tenha alterado apenas
        # num_groups sem informar group_sizes manualmente
        if "group_sizes" not in (configuration or {}):
            resolved["group_sizes"] = _distribute_evenly(team_count, num_groups)
        else:
            if sum(resolved["group_sizes"]) != team_count:
                raise BusinessException(
                    "A soma dos tamanhos de grupo informados deve ser igual ao "
                    "número de times aprovados"
                )
            if len(resolved["group_sizes"]) != num_groups:
                raise BusinessException(
                    "A quantidade de tamanhos de grupo informados deve ser igual "
                    "ao número de grupos"
                )

    if modality_format == ModalityFormat.ROUND_ROBIN:
        rounds = resolved.get("rounds", 1)
        if rounds not in (1, 2):
            raise BusinessException(
                "Número de turnos inválido para Todos Contra Todos (use 1 ou 2)"
            )
        resolved["rounds"] = rounds

    if modality_format == ModalityFormat.TRIANGULAR:
        resolved["double_round"] = bool(resolved.get("double_round", False))

    return resolved
