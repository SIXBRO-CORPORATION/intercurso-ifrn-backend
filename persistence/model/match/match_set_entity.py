from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from persistence.model.abstract_entity import AbstractEntity

from alembic_utils.pg_function import PGFunction
from alembic_utils.pg_trigger import PGTrigger


class MatchSetEntity(AbstractEntity):
    __tablename__ = "match_sets"
    __table_args__ = (
        UniqueConstraint("match_id", "set_number", name="uq_match_sets_match_id_set_number"),
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
            RAISE EXCEPTION
                'match_sets is immutable: UPDATE is not allowed (id=%)',
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
