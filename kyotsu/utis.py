import re
from collections.abc import Collection

from kyotsu.db import Prefix
from sqlalchemy import select, literal_column, Select, text

error_code_pattern = re.compile(r"(?P<prefixes>[a-zA-Z.]+)(?P<increment>\d+)")


def parse_error_code(code: str) -> tuple[list[str], int]:
    match_dict = error_code_pattern.match(code).groupdict()
    groups = match_dict["prefixes"].split(".")
    increment = int(match_dict["increment"])
    return groups, increment


def cumulate_prefixes(prefixes: list[str]) -> list[str]:
    if not prefixes:
        return []
    current = ".".join(prefixes)
    return [current] + cumulate_prefixes(prefixes[1:])


def get_prefix_ids_by_composed_key_query(prefixes: list[str]) -> Select[tuple[int]]:
    anchor = select(
        Prefix.id,
        Prefix.prefix,
        Prefix.prefix.label('composed_prefix'),
        Prefix.parent_prefix_id
    ).where(Prefix.parent_prefix_id.is_(None)).cte(name='composed_prefix', recursive=True)

    recursive = select(
        Prefix.id,
        Prefix.prefix,
        (anchor.c.composed_prefix + text("'.'") + Prefix.prefix).label('composed_prefix'),
        Prefix.parent_prefix_id
    ).select_from(
        Prefix.__table__.join(anchor, Prefix.parent_prefix_id == anchor.c.id)
    )

    anchor = anchor.union_all(recursive)

    final_query = select(anchor.c.id).where(anchor.c.composed_prefix == ".".join(prefixes)).order_by(
        anchor.c.composed_prefix)

    return final_query
