from kyotsu.db.mixins import get_onupdate_function, get_table_trigger

from .models import Prefix, EventCode

from alembic_utils.pg_trigger import PGTrigger
from alembic_utils.pg_function import PGFunction

__all__ = [
    "onupdate_function",
    "prefix_onupdate_trigger",
    "event_code_onupdate_trigger",
    "event_code_auto_increment",
    "event_code_auto_increment_trigger",
]

onupdate_function = get_onupdate_function()
"""Create generic psql function that return `now()` value."""
prefix_onupdate_trigger = get_table_trigger(Prefix.__tablename__)
"""Apply `onupdate_function` to `updated_at` column of `prefixes` table."""
event_code_onupdate_trigger = get_table_trigger(EventCode.__tablename__)
"""Apply `onupdate_function` to `updated_at` column of `error_codes` table."""

event_code_auto_increment = PGFunction(
    schema="public",
    signature="auto_event_code_increment_function()",
    definition=(
        f"RETURNS TRIGGER AS $$ "
        f"BEGIN "
        f"    SELECT COALESCE(MAX(increment), 0) + 1 INTO NEW.increment "
        f"    FROM {EventCode.__tablename__} "
        f"    WHERE prefix_id = NEW.prefix_id;"
        f""
        f"    RETURN NEW;"
        f"END; "
        f"$$ language 'plpgsql';"
    ),
)

event_code_auto_increment_trigger = PGTrigger(
    schema="public",
    signature="trg_auto_increment",
    on_entity=f"public.{EventCode.__tablename__}",
    is_constraint=False,
    definition=(
        "    BEFORE INSERT "
        f"    ON {EventCode.__tablename__} "
        "    FOR EACH ROW "
        " EXECUTE FUNCTION "
        "    auto_event_code_increment_function();"
    )
)