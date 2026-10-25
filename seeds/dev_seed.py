import asyncio
import os
import random
import secrets
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select, update

from domain.enums.bracket_status import BracketStatus
from domain.enums.card_type import CardType
from domain.enums.donation_status import DonationStatus
from domain.enums.event_type import EventType
from domain.enums.gender import Gender
from domain.enums.match_category import MatchCategory
from domain.enums.match_status import MatchStatus
from domain.enums.match_type import MatchType
from domain.enums.modality_format import ModalityFormat
from domain.enums.modality_gender_mode import ModalityGenderMode
from domain.enums.score_type import ScoreType
from domain.enums.season_status import SeasonStatus
from domain.enums.team_member_role import TeamMemberRole
from domain.enums.team_status import TeamStatus
from domain.enums.user_role import UserRole
from persistence.database import AsyncSessionLocal, close_db
from persistence.model.abstract_entity import Base
from persistence.model import (
    BracketEntity,
    BracketGroupEntity,
    BracketGroupTeamEntity,
    MatchEntity,
    MatchEventEntity,
    MatchSetEntity,
    ModalityConfigurationEntity,
    ModalityEntity,
    SeasonEntity,
    SeasonModalityEntity,
    TeamEntity,
    TeamMemberEntity,
    UserEntity,
    VolleyballModalityConfigurationEntity,
)

ADMIN_SERIAL = 1
MONITOR_SERIALS = (2, 3)
MALE_BASE_SERIAL = 100
FEMALE_BASE_SERIAL = 200
PLAYERS_PER_GENDER = 24

MALE_NAMES = [
    "Lucas", "Mateus", "Gabriel", "Pedro", "Rafael", "Felipe", "Bruno", "Thiago",
    "Gustavo", "Daniel", "Henrique", "Vinicius", "Caio", "Davi", "Leonardo", "Rodrigo",
    "Eduardo", "Arthur", "Samuel", "Igor", "Nicolas", "Otávio", "Renan", "Yuri",
]
FEMALE_NAMES = [
    "Ana", "Beatriz", "Camila", "Daniela", "Eduarda", "Fernanda", "Giovana", "Helena",
    "Isabela", "Julia", "Larissa", "Mariana", "Natália", "Olívia", "Patrícia", "Rafaela",
    "Sofia", "Tatiana", "Valentina", "Yasmin", "Alice", "Bianca", "Clara", "Débora",
]
SURNAMES = [
    "Silva", "Souza", "Oliveira", "Santos", "Lima", "Pereira", "Costa", "Ferreira",
    "Rodrigues", "Almeida", "Nascimento", "Araújo", "Ribeiro", "Carvalho", "Gomes", "Martins",
    "Barbosa", "Rocha", "Dias", "Moura", "Cavalcanti", "Fonseca", "Medeiros", "Pinheiro",
]
COURSES = ["Informática", "Eletrotécnica", "Mecânica", "Edificações"]
TEAM_NAMES = ["Computaria", "Eletro FC", "Mecânica Pesada", "Edificações United"]

REGULAR = MatchType.REGULAR
SEMI = MatchType.SEMIFINAL
THIRD = MatchType.THIRD_PLACE
FINAL = MatchType.FINAL
GROUP = MatchCategory.GROUP
KNOCKOUT = MatchCategory.KNOCKOUT
DONE = MatchStatus.FINISHED
LIVE = MatchStatus.IN_PROGRESS
TODO = MatchStatus.SCHEDULED


@dataclass(frozen=True)
class ModalitySpec:
    name: str
    gender_mode: ModalityGenderMode
    min_members: int
    max_members: int
    min_male: Optional[int]
    min_female: Optional[int]
    num_periods: int
    period_minutes: int
    score_type: ScoreType
    males_per_team: int
    females_per_team: int
    volleyball: Optional[Tuple[int, int, int]] = None


MODALITIES = [
    ModalitySpec("Futsal", ModalityGenderMode.MALE, 5, 10, None, None, 2, 20, ScoreType.GOALS, 5, 0),
    ModalitySpec("Vôlei", ModalityGenderMode.MIXED, 6, 12, 2, 2, 1, 90, ScoreType.SETS, 3, 3, (25, 15, 2)),
    ModalitySpec("Basquete", ModalityGenderMode.MIXED, 5, 10, 1, 1, 4, 10, ScoreType.POINTS, 3, 2),
    ModalitySpec("Handebol", ModalityGenderMode.MIXED, 7, 12, 2, 2, 2, 25, ScoreType.GOALS, 4, 3),
]


@dataclass
class MatchPlan:
    team1: Optional[int]
    team2: Optional[int]
    match_type: MatchType
    category: MatchCategory
    status: MatchStatus
    minutes: int
    score: Tuple[int, int] = (0, 0)
    sets: List[Tuple[int, int]] = field(default_factory=list)
    next_index: Optional[int] = None
    current_period: int = 1
    clock_seconds: int = 0
    monitor: int = 0
    cards: List[Tuple[int, int, CardType, int]] = field(default_factory=list)


@dataclass
class BracketPlan:
    format: ModalityFormat
    configuration: dict
    with_group: bool
    matches: List[MatchPlan]


ACTIVE_PLANS: Dict[str, BracketPlan] = {
    "Futsal": BracketPlan(
        ModalityFormat.ROUND_ROBIN,
        {"rounds": 1},
        True,
        [
            MatchPlan(0, 1, REGULAR, GROUP, DONE, -300, score=(4, 2), cards=[(2, 1, CardType.YELLOW, 900)]),
            MatchPlan(2, 3, REGULAR, GROUP, DONE, -240, score=(2, 2)),
            MatchPlan(0, 2, REGULAR, GROUP, LIVE, -30, score=(1, 0), current_period=2, clock_seconds=1500),
            MatchPlan(1, 3, REGULAR, GROUP, TODO, 60),
            MatchPlan(0, 3, REGULAR, GROUP, TODO, 1500),
            MatchPlan(1, 2, REGULAR, GROUP, TODO, 1560),
        ],
    ),
    "Vôlei": BracketPlan(
        ModalityFormat.ROUND_ROBIN,
        {"rounds": 1},
        True,
        [
            MatchPlan(0, 1, REGULAR, GROUP, DONE, -300, sets=[(25, 20), (25, 18)]),
            MatchPlan(2, 3, REGULAR, GROUP, DONE, -240, sets=[(25, 23), (22, 25), (15, 12)]),
            MatchPlan(0, 2, REGULAR, GROUP, LIVE, -50, score=(12, 9), sets=[(25, 21)], clock_seconds=2400, monitor=1),
            MatchPlan(1, 3, REGULAR, GROUP, TODO, 60),
            MatchPlan(0, 3, REGULAR, GROUP, TODO, 1500),
            MatchPlan(1, 2, REGULAR, GROUP, TODO, 1560),
        ],
    ),
    "Basquete": BracketPlan(
        ModalityFormat.KNOCKOUT,
        {"has_third_place": True},
        False,
        [
            MatchPlan(0, 3, SEMI, KNOCKOUT, DONE, -200, score=(54, 48), next_index=2),
            MatchPlan(1, 2, SEMI, KNOCKOUT, TODO, 120, next_index=2),
            MatchPlan(0, None, FINAL, KNOCKOUT, TODO, 1500),
            MatchPlan(3, None, THIRD, KNOCKOUT, TODO, 1440),
        ],
    ),
    "Handebol": BracketPlan(
        ModalityFormat.KNOCKOUT,
        {"has_third_place": True},
        False,
        [
            MatchPlan(0, 1, SEMI, KNOCKOUT, TODO, 90, next_index=2),
            MatchPlan(2, 3, SEMI, KNOCKOUT, TODO, 210, next_index=2),
            MatchPlan(None, None, FINAL, KNOCKOUT, TODO, 1500),
            MatchPlan(None, None, THIRD, KNOCKOUT, TODO, 1440),
        ],
    ),
}

PAST_PLANS: Dict[str, MatchPlan] = {
    "Futsal": MatchPlan(0, 1, FINAL, KNOCKOUT, DONE, -576000, score=(3, 1)),
    "Vôlei": MatchPlan(0, 1, FINAL, KNOCKOUT, DONE, -576000, sets=[(25, 22), (23, 25), (25, 20)]),
    "Basquete": MatchPlan(0, 1, FINAL, KNOCKOUT, DONE, -576000, score=(61, 57)),
    "Handebol": MatchPlan(0, 1, FINAL, KNOCKOUT, DONE, -576000, score=(22, 25)),
}


@dataclass
class UserPool:
    admin: UserEntity
    monitors: List[UserEntity]
    males: List[UserEntity]
    females: List[UserEntity]

    def all(self) -> List[UserEntity]:
        return [self.admin, *self.monitors, *self.males, *self.females]


def matricula_of(serial: int) -> str:
    return f"2026{serial:07d}"


def new_user(
    serial: int,
    name: str,
    gender: Gender,
    role: UserRole,
    user_type: str,
    athlete: bool,
    index: int = 0,
) -> UserEntity:
    matricula = matricula_of(serial)
    return UserEntity(
        id=uuid4(),
        name=name,
        email=f"{matricula}@seed.intercurso.local",
        cpf=f"999{serial:08d}",
        matricula=matricula,
        atleta=athlete,
        role=role.value,
        gender=gender.value,
        tipo_usuario=user_type,
        campus="Natal - Central",
        curso=f"Técnico em {COURSES[index % len(COURSES)]}",
        turno="Matutino",
        email_classroom=f"{matricula}@seed.intercurso.local",
        birth_date=date(2007, 1, 1) + timedelta(days=index * 17),
        frequencia_percentual=90,
    )


def build_users() -> UserPool:
    admin = new_user(ADMIN_SERIAL, "Admin Seed", Gender.MALE, UserRole.ADMIN, "Servidor", False)
    monitors = [
        new_user(MONITOR_SERIALS[0], "Monitor Seed Um", Gender.FEMALE, UserRole.MONITOR, "Servidor", False),
        new_user(MONITOR_SERIALS[1], "Monitor Seed Dois", Gender.MALE, UserRole.MONITOR, "Servidor", False),
    ]
    males = [
        new_user(
            MALE_BASE_SERIAL + i,
            f"{MALE_NAMES[i]} {SURNAMES[(i * 7) % len(SURNAMES)]}",
            Gender.MALE,
            UserRole.USER,
            "Aluno",
            True,
            i,
        )
        for i in range(PLAYERS_PER_GENDER)
    ]
    females = [
        new_user(
            FEMALE_BASE_SERIAL + i,
            f"{FEMALE_NAMES[i]} {SURNAMES[(i * 5 + 3) % len(SURNAMES)]}",
            Gender.FEMALE,
            UserRole.USER,
            "Aluno",
            True,
            i,
        )
        for i in range(PLAYERS_PER_GENDER)
    ]
    return UserPool(admin, monitors, males, females)


def pick_roster(pool: UserPool, spec: ModalitySpec, modality_index: int, team_index: int) -> List[UserEntity]:
    shift = modality_index * 5
    males = [
        pool.males[(shift + team_index * spec.males_per_team + k) % len(pool.males)]
        for k in range(spec.males_per_team)
    ]
    females = [
        pool.females[(shift + team_index * spec.females_per_team + k) % len(pool.females)]
        for k in range(spec.females_per_team)
    ]
    return [*males, *females]


def build_modality(spec: ModalitySpec) -> Tuple[ModalityEntity, List[object]]:
    modality = ModalityEntity(
        id=uuid4(),
        name=spec.name,
        min_members=spec.min_members,
        max_members=spec.max_members,
        gender_mode=spec.gender_mode.value,
        min_male_members=spec.min_male,
        min_female_members=spec.min_female,
    )
    configuration = ModalityConfigurationEntity(
        id=uuid4(),
        modality_id=modality.id,
        num_periods=spec.num_periods,
        period_durations_minutes=spec.period_minutes,
        score_type=spec.score_type.value,
        metadata_json=None,
    )
    created: List[object] = [modality, configuration]
    if spec.volleyball is not None:
        points_per_set, final_set_points, sets_to_win = spec.volleyball
        created.append(
            VolleyballModalityConfigurationEntity(
                id=uuid4(),
                modality_configuration_id=configuration.id,
                points_per_set=points_per_set,
                final_set_points=final_set_points,
                sets_to_win=sets_to_win,
            )
        )
    return modality, created


def build_team(
    season: SeasonEntity,
    modality_id: UUID,
    name: str,
    roster: List[UserEntity],
    admin: UserEntity,
) -> Tuple[TeamEntity, List[TeamMemberEntity]]:
    submitted_at = season.registration_end_date - timedelta(days=3)
    approved_at = season.registration_end_date - timedelta(days=1)
    team = TeamEntity(
        id=uuid4(),
        name=name,
        season_id=season.id,
        modality_id=modality_id,
        owner_id=roster[0].id,
        captain_id=roster[1].id if len(roster) > 1 else roster[0].id,
        status=TeamStatus.APPROVED.value,
        invite_token=secrets.token_urlsafe(16),
        token_active=True,
        photo=None,
        submitted_at=submitted_at,
        approved_at=approved_at,
        approved_by=admin.id,
    )
    members = [
        TeamMemberEntity(
            id=uuid4(),
            team_id=team.id,
            user_id=user.id,
            role=(TeamMemberRole.OWNER if index == 0 else TeamMemberRole.MEMBER).value,
            donation_status=DonationStatus.DONATION_CONFIRMED.value,
            donation_confirmed_at=submitted_at,
            donation_confirmed_by=admin.id,
            joined_at=season.registration_start_date + timedelta(days=1),
        )
        for index, user in enumerate(roster)
    ]
    return team, members


def apply_result(home: BracketGroupTeamEntity, away: BracketGroupTeamEntity, home_goals: int, away_goals: int) -> None:
    home.goals_for += home_goals
    home.goals_against += away_goals
    away.goals_for += away_goals
    away.goals_against += home_goals
    if home_goals > away_goals:
        home.points += 3
        home.wins += 1
        away.losses += 1
    elif away_goals > home_goals:
        away.points += 3
        away.wins += 1
        home.losses += 1
    else:
        home.points += 1
        away.points += 1
        home.draws += 1
        away.draws += 1
    home.goals_difference = home.goals_for - home.goals_against
    away.goals_difference = away.goals_for - away.goals_against


def build_events(
    rng: random.Random,
    match: MatchEntity,
    plan: MatchPlan,
    spec: ModalitySpec,
    rosters: List[List[UUID]],
    team_ids: List[UUID],
    monitor_id: UUID,
    goals: Tuple[int, int],
) -> List[MatchEventEntity]:
    events: List[MatchEventEntity] = []

    def add(event_type: EventType, clock: int, team_id=None, player_id=None, metadata=None) -> None:
        events.append(
            MatchEventEntity(
                id=uuid4(),
                match_id=match.id,
                team_id=team_id,
                player_id=player_id,
                event_type=event_type.value,
                clock_seconds=clock,
                metadata_json=metadata,
            )
        )

    add(EventType.MATCH_STARTED, 0, metadata={"monitor_id": str(monitor_id)})
    total = match.clock_seconds

    if spec.score_type == ScoreType.SETS:
        won = [0, 0]
        for number, (points1, points2) in enumerate(plan.sets, start=1):
            side = 0 if points1 > points2 else 1
            won[side] += 1
            add(
                EventType.SET_END,
                min(total, number * 1500),
                team_id=team_ids[plan.team1 if side == 0 else plan.team2],
                metadata={
                    "set_number": number,
                    "score": f"{points1}x{points2}",
                    "winner_team_id": str(team_ids[plan.team1 if side == 0 else plan.team2]),
                    "team1_sets_won": won[0],
                    "team2_sets_won": won[1],
                },
            )
    else:
        period_length = spec.period_minutes * 60
        periods_done = spec.num_periods if plan.status == DONE else plan.current_period - 1
        for period in range(1, periods_done + 1):
            add(EventType.PERIOD_END, period * period_length, metadata={"period": period})
            if period < spec.num_periods:
                add(EventType.PERIOD_START, period * period_length, metadata={"period": period + 1})
        event_type = EventType.GOAL if spec.score_type == ScoreType.GOALS else EventType.POINT
        for side, scored in enumerate(goals):
            team_index = plan.team1 if side == 0 else plan.team2
            for _ in range(scored):
                add(
                    event_type,
                    rng.randint(30, max(31, total - 1)),
                    team_id=team_ids[team_index],
                    player_id=rng.choice(rosters[team_index]),
                )
        for side, roster_index, card, clock in plan.cards:
            team_index = plan.team1 if side == 1 else plan.team2
            add(
                EventType.CARD_YELLOW if card == CardType.YELLOW else EventType.CARD_RED,
                clock,
                team_id=team_ids[team_index],
                player_id=rosters[team_index][roster_index],
                metadata={"previous_cards": 0},
            )

    if plan.status == DONE:
        add(
            EventType.MATCH_END,
            total,
            metadata={"winner_id": str(match.winner_id)} if match.winner_id else {},
        )

    events.sort(key=lambda event: event.clock_seconds)
    return events


def build_bracket(
    rng: random.Random,
    now: datetime,
    season: SeasonEntity,
    modality_id: UUID,
    spec: ModalitySpec,
    bracket_plan: BracketPlan,
    bracket_status: BracketStatus,
    team_ids: List[UUID],
    rosters: List[List[UUID]],
    admin: UserEntity,
    monitors: List[UserEntity],
) -> List[object]:
    bracket = BracketEntity(
        id=uuid4(),
        season_id=season.id,
        modality_id=modality_id,
        format=bracket_plan.format.value,
        configuration=bracket_plan.configuration,
        status=bracket_status.value,
        created_by=admin.id,
    )
    entities: List[object] = [bracket]
    group = None
    standings: Dict[UUID, BracketGroupTeamEntity] = {}
    if bracket_plan.with_group:
        group = BracketGroupEntity(id=uuid4(), bracket_id=bracket.id, name="Geral", display_order=0)
        entities.append(group)
        for team_id in team_ids:
            standing = BracketGroupTeamEntity(
                id=uuid4(),
                bracket_group_id=group.id,
                team_id=team_id,
                points=0,
                wins=0,
                draws=0,
                losses=0,
                goals_for=0,
                goals_against=0,
                goals_difference=0,
            )
            standings[team_id] = standing
            entities.append(standing)

    is_sets = spec.score_type == ScoreType.SETS
    period_length = spec.period_minutes * 60
    match_ids = [uuid4() for _ in bracket_plan.matches]
    matches: List[MatchEntity] = []
    children: List[object] = []

    for index, plan in enumerate(bracket_plan.matches):
        team1_id = team_ids[plan.team1] if plan.team1 is not None else None
        team2_id = team_ids[plan.team2] if plan.team2 is not None else None
        scheduled = now + timedelta(minutes=plan.minutes)
        monitor = monitors[plan.monitor]
        goals = plan.score
        sets_won1 = sets_won2 = None
        score1, score2 = plan.score
        clock = 0
        period = 1
        started = finished = winner = None

        if plan.status != TODO:
            started = scheduled
            if is_sets:
                sets_won1 = sum(1 for a, b in plan.sets if a > b)
                sets_won2 = len(plan.sets) - sets_won1
                goals = (sets_won1, sets_won2)
            if plan.status == DONE:
                clock = plan.clock_seconds or (len(plan.sets) * 1500 if is_sets else spec.num_periods * period_length)
                period = 1 if is_sets else spec.num_periods
                finished = started + timedelta(seconds=clock)
                if is_sets:
                    score1, score2 = 0, 0
                winner = team1_id if goals[0] > goals[1] else team2_id if goals[1] > goals[0] else None
            else:
                clock = plan.clock_seconds
                period = plan.current_period

        match = MatchEntity(
            id=match_ids[index],
            bracket_id=bracket.id,
            bracket_group_id=group.id if group is not None else None,
            team1_id=team1_id,
            team2_id=team2_id,
            winner_id=winner,
            next_match_id=match_ids[plan.next_index] if plan.next_index is not None else None,
            monitor_id=monitor.id if plan.status != TODO else None,
            match_type=plan.match_type.value,
            match_category=plan.category.value,
            status=plan.status.value,
            scheduled_date=scheduled,
            started_at=started,
            finished_at=finished,
            team1_score=score1,
            team2_score=score2,
            penality_result=None,
            clock_seconds=clock,
            clock_running=False,
            current_period=period,
            is_bye=False,
            metadata_json=None,
            team1_sets_won=sets_won1,
            team2_sets_won=sets_won2,
            penalty_shootout_active=False,
            team1_penalty_score=None,
            team2_penalty_score=None,
        )
        matches.append(match)

        if plan.status != TODO:
            children.extend(
                build_events(rng, match, plan, spec, rosters, team_ids, monitor.id, goals)
            )
            if is_sets:
                for number, (points1, points2) in enumerate(plan.sets, start=1):
                    children.append(
                        MatchSetEntity(
                            id=uuid4(),
                            match_id=match.id,
                            set_number=number,
                            team1_points=points1,
                            team2_points=points2,
                            winner_team_id=team1_id if points1 > points2 else team2_id,
                        )
                    )

        if plan.status == DONE and group is not None:
            apply_result(standings[team1_id], standings[team2_id], goals[0], goals[1])

    entities.extend(reversed(matches))
    entities.extend(children)
    return entities


def build_season(
    rng: random.Random,
    now: datetime,
    season: SeasonEntity,
    modality_ids: Dict[str, UUID],
    pool: UserPool,
    team_count: int,
    plan_for,
    bracket_status: BracketStatus,
) -> List[object]:
    entities: List[object] = [season]
    for spec in MODALITIES:
        entities.append(
            SeasonModalityEntity(id=uuid4(), season_id=season.id, modality_id=modality_ids[spec.name])
        )

    for modality_index, spec in enumerate(MODALITIES):
        team_ids: List[UUID] = []
        rosters: List[List[UUID]] = []
        for team_index in range(team_count):
            roster = pick_roster(pool, spec, modality_index, team_index)
            team, members = build_team(
                season, modality_ids[spec.name], TEAM_NAMES[team_index], roster, pool.admin
            )
            entities.append(team)
            entities.extend(members)
            team_ids.append(team.id)
            rosters.append([user.id for user in roster])
        entities.extend(
            build_bracket(
                rng,
                now,
                season,
                modality_ids[spec.name],
                spec,
                plan_for(spec.name),
                bracket_status,
                team_ids,
                rosters,
                pool.admin,
                pool.monitors,
            )
        )
    return entities


def build_seasons(now: datetime, admin: UserEntity) -> Tuple[SeasonEntity, SeasonEntity]:
    current = SeasonEntity(
        id=uuid4(),
        name=f"Intercurso {now.year}",
        year=now.year,
        status=SeasonStatus.IN_PROGRESS.value,
        registration_start_date=now - timedelta(days=60),
        registration_end_date=now - timedelta(days=30),
        registration_opened_at=now - timedelta(days=60),
        registration_closed_at=now - timedelta(days=30),
        started_at=now - timedelta(days=7),
        finished_at=None,
        rules_document=None,
        created_by=admin.id,
        active=True,
    )
    past = SeasonEntity(
        id=uuid4(),
        name=f"Intercurso {now.year - 1}",
        year=now.year - 1,
        status=SeasonStatus.FINISHED.value,
        registration_start_date=now - timedelta(days=430),
        registration_end_date=now - timedelta(days=400),
        registration_opened_at=now - timedelta(days=430),
        registration_closed_at=now - timedelta(days=400),
        started_at=now - timedelta(days=390),
        finished_at=now - timedelta(days=380),
        rules_document=None,
        created_by=admin.id,
        active=False,
    )
    return current, past


async def ensure_modalities(session) -> Tuple[Dict[str, UUID], List[object]]:
    modality_ids: Dict[str, UUID] = {}
    created: List[object] = []
    for spec in MODALITIES:
        existing = await session.scalar(select(ModalityEntity).where(ModalityEntity.name == spec.name))
        if existing is not None:
            modality_ids[spec.name] = existing.id
            continue
        modality, entities = build_modality(spec)
        modality_ids[spec.name] = modality.id
        created.extend(entities)
    return modality_ids, created


async def promote_real_user(session, matricula: str) -> None:
    user = await session.scalar(select(UserEntity).where(UserEntity.matricula == matricula))
    if user is None:
        print(f"Usuário {matricula} não encontrado. Faça login uma vez e rode a seed de novo.")
        return
    user.role = UserRole.ADMIN.value
    seed_monitor_id = await session.scalar(
        select(UserEntity.id).where(UserEntity.matricula == matricula_of(MONITOR_SERIALS[0]))
    )
    if seed_monitor_id is not None:
        await session.execute(
            update(MatchEntity)
            .where(
                MatchEntity.monitor_id == seed_monitor_id,
                MatchEntity.status == MatchStatus.IN_PROGRESS.value,
            )
            .values(monitor_id=user.id)
        )
    print(f"Usuário {matricula} promovido a ADMIN e responsável pela partida em andamento.")


async def run() -> None:
    now = datetime.now(timezone.utc)
    rng = random.Random(2026)
    real_matricula = os.getenv("SEED_ADMIN_MATRICULA")

    async with AsyncSessionLocal() as session:
        already_seeded = await session.scalar(
            select(UserEntity.id).where(UserEntity.matricula == matricula_of(ADMIN_SERIAL))
        )

        if already_seeded is not None:
            print("Seed já aplicada. Para recriar do zero: docker compose -f docker-compose.dev.yml down -v")
        else:
            other_active = await session.scalar(
                select(SeasonEntity.id).where(
                    SeasonEntity.active.is_(True), SeasonEntity.deleted_at.is_(None)
                )
            )
            if other_active is not None:
                raise SystemExit("Já existe uma temporada ativa no banco. A seed exige banco sem temporada ativa.")

            pool = build_users()
            modality_ids, modality_entities = await ensure_modalities(session)
            current, past = build_seasons(now, pool.admin)

            entities: List[object] = [*pool.all(), *modality_entities]
            entities.extend(
                build_season(
                    rng, now, current, modality_ids, pool, 4,
                    lambda name: ACTIVE_PLANS[name], BracketStatus.ACTIVE,
                )
            )
            entities.extend(
                build_season(
                    rng, now, past, modality_ids, pool, 2,
                    lambda name: BracketPlan(
                        ModalityFormat.KNOCKOUT, {"has_third_place": False}, False, [PAST_PLANS[name]]
                    ),
                    BracketStatus.FINISHED,
                )
            )
            for table in Base.metadata.sorted_tables:
                batch = [entity for entity in entities if entity.__table__ is table]
                if batch:
                    session.add_all(batch)
                    await session.flush()

            summary = Counter(type(entity).__name__.replace("Entity", "") for entity in entities)
            print("Seed aplicada: " + ", ".join(f"{name}={count}" for name, count in sorted(summary.items())))

        if real_matricula:
            await promote_real_user(session, real_matricula)

        await session.commit()

    await close_db()


if __name__ == "__main__":
    asyncio.run(run())