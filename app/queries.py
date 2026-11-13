from typing import Optional
from app.database import get_cursor


def get_all_gosts() -> list[dict]:
    with get_cursor() as cur:
        cur.execute("""
            SELECT g.*, COUNT(f.id) AS fastener_count
            FROM gosts g
            LEFT JOIN fasteners f ON f.gost_number = g.number
            GROUP BY g.id
            ORDER BY g.number
        """)
        return [dict(r) for r in cur.fetchall()]


def search_fasteners(
    type_name: Optional[str] = None,
    d: Optional[float] = None,
    d1: Optional[float] = None,
    l_min: Optional[float] = None,
    l_max: Optional[float] = None,
    gost_number: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
) -> tuple[list[dict], int]:
    conditions: list[str] = []
    params: list = []

    if type_name:
        conditions.append("f.type_name = %s")
        params.append(type_name)
    if d is not None:
        conditions.append("(f.params->>'d')::numeric = %s")
        params.append(d)
    if d1 is not None:
        conditions.append("(f.params->>'d1')::numeric = %s")
        params.append(d1)
    if l_min is not None:
        conditions.append("(f.params->>'l')::numeric >= %s")
        params.append(l_min)
    if l_max is not None:
        conditions.append("(f.params->>'l')::numeric <= %s")
        params.append(l_max)
    if gost_number:
        conditions.append("f.gost_number = %s")
        params.append(gost_number)
    if q:
        conditions.append(
            "(f.name ILIKE %s OR f.gost_number ILIKE %s OR f.type_name ILIKE %s)"
        )
        like = f"%{q}%"
        params.extend([like, like, like])

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    sql = f"""
        SELECT
            f.id,
            f.type_name,
            f.name,
            f.gost_number,
            f.params,
            (f.params->>'d')::numeric        AS d,
            (f.params->>'d1')::numeric       AS d1,
            (f.params->>'l')::numeric        AS l,
            (f.params->>'P_coarse')::numeric AS pitch,
            f.params->>'tolerance'           AS tolerance,
            f.params->>'strength'            AS strength
        FROM fasteners f
        {where}
    """

    with get_cursor() as cur:
        cur.execute(f"SELECT COUNT(*) AS cnt FROM fasteners f {where}", params)
        total = cur.fetchone()["cnt"]

        cur.execute(
            sql + " ORDER BY (f.params->>'d')::numeric,"
            " (f.params->>'l')::numeric NULLS LAST"
            " LIMIT %s OFFSET %s",
            params + [limit, offset],
        )
        rows = [dict(r) for r in cur.fetchall()]

    return rows, total


def get_stats() -> dict:
    with get_cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(*)                        AS total,
                COUNT(DISTINCT type_name)       AS types_count,
                COUNT(DISTINCT gost_number)     AS gosts_count,
                MIN((params->>'d')::numeric)    AS d_min,
                MAX((params->>'d')::numeric)    AS d_max
            FROM fasteners
        """)
        return dict(cur.fetchone())


def get_type_list() -> list[str]:
    with get_cursor() as cur:
        cur.execute("SELECT DISTINCT type_name FROM fasteners ORDER BY type_name")
        return [r["type_name"] for r in cur.fetchall()]


def get_gost_numbers() -> list[str]:
    with get_cursor() as cur:
        cur.execute("SELECT number FROM gosts ORDER BY number")
        return [r["number"] for r in cur.fetchall()]
