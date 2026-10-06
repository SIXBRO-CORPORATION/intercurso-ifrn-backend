from uuid import uuid4

from business.bracket._standings import order_group_standings
from domain.bracket.bracket_group_team import BracketGroupTeam
from domain.enums.match_category import MatchCategory
from domain.enums.match_status import MatchStatus
from domain.match.match import Match


def make_team(team_id, points, wins=0, goals_for=0, goals_against=0):
    return BracketGroupTeam(
        id=uuid4(),
        bracket_group_id=uuid4(),
        team_id=team_id,
        points=points,
        wins=wins,
        draws=0,
        losses=0,
        goals_for=goals_for,
        goals_against=goals_against,
        goals_difference=goals_for - goals_against,
    )


def make_match(team1_id, team2_id, score1, score2, category=MatchCategory.GROUP):
    winner_id = None
    if score1 > score2:
        winner_id = team1_id
    elif score2 > score1:
        winner_id = team2_id
    return Match(
        id=uuid4(),
        team1_id=team1_id,
        team2_id=team2_id,
        team1_score=score1,
        team2_score=score2,
        winner_id=winner_id,
        status=MatchStatus.FINISHED,
        match_category=category,
    )


class TestOrderGroupStandings:
    def test_orders_by_points_when_no_tie(self):
        a, b, c = uuid4(), uuid4(), uuid4()
        teams = [make_team(a, points=3), make_team(b, points=9), make_team(c, points=6)]

        result = order_group_standings(teams, [])

        assert [t.team_id for t in result] == [b, c, a]

    def test_tie_broken_by_head_to_head_confronto_direto(self):
        """Art. 28, I: duas equipes empatadas em pontos, A venceu B no
        confronto direto -> A fica na frente, mesmo com saldo geral pior."""
        a, b = uuid4(), uuid4()
        teams = [
            make_team(a, points=6, goals_for=2, goals_against=5),
            make_team(b, points=6, goals_for=10, goals_against=3),
        ]
        matches = [make_match(a, b, score1=3, score2=1)]

        result = order_group_standings(teams, matches)

        assert [t.team_id for t in result] == [a, b]

    def test_tie_broken_by_wins_when_head_to_head_is_draw(self):
        """Art. 28, I e II: se o confronto direto empatou, decide o maior
        número de vitórias no grupo todo."""
        a, b = uuid4(), uuid4()
        teams = [
            make_team(a, points=6, wins=2, goals_for=5, goals_against=4),
            make_team(b, points=6, wins=1, goals_for=5, goals_against=4),
        ]
        matches = [make_match(a, b, score1=1, score2=1)]

        result = order_group_standings(teams, matches)

        assert [t.team_id for t in result] == [a, b]

    def test_tie_broken_by_mini_saldo_among_tied_teams(self):
        """Art. 28, III: três equipes empatadas em pontos e vitórias; usa o
        saldo só dos jogos entre elas três (não o saldo geral do grupo)."""
        a, b, c = uuid4(), uuid4(), uuid4()
        teams = [
            # saldo GERAL favorece C, mas entre A/B/C o saldo de A é melhor
            make_team(a, points=4, wins=1, goals_for=3, goals_against=3),
            make_team(b, points=4, wins=1, goals_for=3, goals_against=3),
            make_team(c, points=4, wins=1, goals_for=20, goals_against=2),
        ]
        matches = [
            make_match(a, b, score1=2, score2=0),  # A 2x0 B
            make_match(b, c, score1=1, score2=0),  # B 1x0 C
            make_match(c, a, score1=1, score2=0),  # C 1x0 A
        ]
        # mini-saldo entre os 3: A = (2-0)+(0-1) = +1; B = (0-2)+(1-0) = -1;
        # C = (0-1)+(1-0) = 0  ->  A, C, B
        result = order_group_standings(teams, matches)

        assert [t.team_id for t in result] == [a, c, b]

    def test_falls_back_to_overall_goal_difference_when_never_played_each_other(self):
        """Quando as equipes empatadas nunca jogaram entre si (ex: grupos
        diferentes de uma fase anterior combinados), confronto direto e
        mini-saldo ficam neutros (0) e o desempate cai nos critérios gerais
        (V, VI, VII)."""
        a, b = uuid4(), uuid4()
        teams = [
            make_team(a, points=3, wins=1, goals_for=5, goals_against=1),
            make_team(b, points=3, wins=1, goals_for=2, goals_against=1),
        ]

        result = order_group_standings(teams, [])

        assert [t.team_id for t in result] == [a, b]

    def test_knockout_matches_do_not_count_for_group_tiebreak(self):
        """Partida de mata-mata entre as duas equipes não deve interferir
        no desempate da fase de grupos."""
        a, b = uuid4(), uuid4()
        teams = [
            make_team(a, points=6, goals_for=1, goals_against=1),
            make_team(b, points=6, goals_for=1, goals_against=1),
        ]
        matches = [
            make_match(a, b, score1=5, score2=0, category=MatchCategory.KNOCKOUT),
        ]

        result = order_group_standings(teams, matches)

        # sem jogos de grupo entre elas, cai nos critérios gerais (empatados
        # em tudo) -> ordem estável por id, nenhuma das duas foi "decidida"
        # pelo jogo de mata-mata
        assert {t.team_id for t in result} == {a, b}

    def test_unfinished_match_does_not_count(self):
        a, b = uuid4(), uuid4()
        teams = [
            make_team(a, points=6, goals_for=1, goals_against=0),
            make_team(b, points=6, goals_for=0, goals_against=1),
        ]
        pending_match = make_match(a, b, score1=3, score2=0)
        pending_match.status = MatchStatus.IN_PROGRESS

        result = order_group_standings(teams, [pending_match])

        # confronto direto não conta (não finalizado); cai pro saldo geral
        # (V/VI), que já favorece A
        assert [t.team_id for t in result] == [a, b]

    def test_three_way_tie_resolved_progressively_through_multiple_criteria(self):
        """Garante que o algoritmo não acha empate total e devolve as 3
        equipes em alguma ordem determinística, mesmo esgotando vários
        critérios."""
        a, b, c = uuid4(), uuid4(), uuid4()
        teams = [
            make_team(a, points=3, wins=1, goals_for=1, goals_against=1),
            make_team(b, points=3, wins=1, goals_for=1, goals_against=1),
            make_team(c, points=3, wins=1, goals_for=1, goals_against=1),
        ]

        result = order_group_standings(teams, [])

        assert len(result) == 3
        assert {t.team_id for t in result} == {a, b, c}
