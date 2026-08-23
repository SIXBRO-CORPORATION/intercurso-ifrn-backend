from sqlalchemy import Column, Index, Integer, ForeignKey, text
from persistence.model.abstract_entity import AbstractEntity

from alembic_utils.pg_function import PGFunction
from alembic_utils.pg_trigger import PGTrigger


class MatchSetEntity(AbstractEntity):
    __tablename__ = "match_sets"
    __table_args__ = (
        Index(
            "uq_match_sets_match_id_set_number",
            "match_id",
            "set_number",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    match_id = Column(ForeignKey("matches.id"), nullable=False)

    set_number = Column(Integer, nullable=False)

    team1_points = Column(Integer, nullable=False)

    team2_points = Column(Integer, nullable=False)

    winner_team_id = Column(ForeignKey("teams.id"), nullable=False)


prevent_match_sets_mutation_fn = PGFunction(
    schema="public",
    signature="prevent_match_sets_mutation()",
    definition="""
    RETURNS trigger AS $$
    BEGIN
        IF TG_OP = 'TRUNCATE' THEN
            RAISE EXCEPTION
                'match_sets is immutable: TRUNCATE is not allowed'
                USING ERRCODE = '23000';
        END IF;

        IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION
                'match_sets is immutable: DELETE is not allowed (id=%)',
                OLD.id
                USING ERRCODE = '23000';
        END IF;

        IF TG_OP = 'UPDATE' THEN
            -- UC017 (RN35 / ADR002 Momento 5): a única mutação permitida numa
            -- linha de match_sets é a transição de soft delete
            -- (deleted_at NULL -> NOT NULL). Nenhuma outra coluna de negócio
            -- pode mudar nesse ou em qualquer outro UPDATE; isso preserva a
            -- garantia original do ADR002 de que um set já registrado nunca é
            -- reescrito silenciosamente, ao mesmo tempo em que viabiliza o
            -- fluxo de correção auditado do UC017.
            IF OLD.deleted_at IS NULL
                AND NEW.deleted_at IS NOT NULL
                AND NEW.match_id IS NOT DISTINCT FROM OLD.match_id
                AND NEW.set_number IS NOT DISTINCT FROM OLD.set_number
                AND NEW.team1_points IS NOT DISTINCT FROM OLD.team1_points
                AND NEW.team2_points IS NOT DISTINCT FROM OLD.team2_points
                AND NEW.winner_team_id IS NOT DISTINCT FROM OLD.winner_team_id
                AND NEW.created_at IS NOT DISTINCT FROM OLD.created_at
                AND NEW.active IS NOT DISTINCT FROM OLD.active
            THEN
                RETURN NEW;
            END IF;

            RAISE EXCEPTION
                'match_sets is immutable: only a soft-delete transition '
                '(deleted_at NULL -> NOT NULL, no other column change) is '
                'allowed (id=%)',
                OLD.id
                USING ERRCODE = '23000';
        END IF;

        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql
    """,
)

match_sets_immutable_trigger = PGTrigger(
    schema="public",
    signature="trg_match_sets_immutable",
    on_entity="public.match_sets",
    is_constraint=False,
    definition="""
    BEFORE UPDATE OR DELETE ON public.match_sets
    FOR EACH ROW
    EXECUTE FUNCTION prevent_match_sets_mutation()
    """,
)

match_sets_immutable_truncate_trigger = PGTrigger(
    schema="public",
    signature="trg_match_sets_immutable_truncate",
    on_entity="public.match_sets",
    is_constraint=False,
    definition="""
    BEFORE TRUNCATE ON public.match_sets
    FOR EACH STATEMENT
    EXECUTE FUNCTION prevent_match_sets_mutation()
    """,
)


PG_ENTITIES = [
    prevent_match_sets_mutation_fn,
    match_sets_immutable_trigger,
    match_sets_immutable_truncate_trigger,
]
