import json
from app.database import get_cursor

DDL = """
CREATE TABLE IF NOT EXISTS gosts (
    id          SERIAL PRIMARY KEY,
    number      VARCHAR(50)  UNIQUE NOT NULL,
    title       TEXT         NOT NULL,
    year        INT,
    description TEXT,
    metadata    JSONB        NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS fasteners (
    id          SERIAL       PRIMARY KEY,
    type_name   VARCHAR(100) NOT NULL,
    name        TEXT         NOT NULL,
    gost_number VARCHAR(50)  NOT NULL REFERENCES gosts(number),
    params      JSONB        NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_gin_params ON fasteners USING GIN(params);
CREATE INDEX IF NOT EXISTS idx_btree_d    ON fasteners (( (params->>'d')::numeric  ));
CREATE INDEX IF NOT EXISTS idx_btree_d1   ON fasteners (( (params->>'d1')::numeric ));
CREATE INDEX IF NOT EXISTS idx_btree_l    ON fasteners (( (params->>'l')::numeric  ));
CREATE INDEX IF NOT EXISTS idx_type_d     ON fasteners (type_name, ( (params->>'d')::numeric ));
"""

GOSTS_DATA = [
    {
        "number": "ГОСТ 22042-76",
        "title": "Шпильки для деталей с гладкими поверхностями",
        "year": 1976,
        "description": (
            "Стандарт распространяется на шпильки с двумя одинаковыми по длине "
            "резьбовыми концами с диаметром резьбы от 2 до 48 мм, класс точности В."
        ),
        "metadata": {"accuracy_class": "В", "thread_type": "метрическая"},
    },
    {
        "number": "ГОСТ 5915-70",
        "title": "Гайки шестигранные класса точности В",
        "year": 1970,
        "description": (
            "Распространяется на шестигранные гайки с диаметром резьбы от 1 до 48 мм, "
            "класс точности В."
        ),
        "metadata": {"accuracy_class": "В", "shape": "шестигранник"},
    },
    {
        "number": "ГОСТ 7798-70",
        "title": "Болты с шестигранной головкой класса точности В",
        "year": 1970,
        "description": (
            "Болты с шестигранной головкой нормальной точности, "
            "диаметр резьбы от 6 до 48 мм."
        ),
        "metadata": {"accuracy_class": "В", "head": "шестигранная"},
    },
    {
        "number": "ГОСТ 1491-80",
        "title": "Шурупы с полукруглой головкой",
        "year": 1980,
        "description": "Шурупы с полукруглой головкой, диаметр от 1 до 10 мм.",
        "metadata": {"head": "полукруглая"},
    },
]


def _pitch(d: float) -> float:
    table = {
        2: 0.4, 2.5: 0.45, 3: 0.5, 4: 0.7, 5: 0.8, 6: 1.0,
        8: 1.25, 10: 1.5, 12: 1.75, 14: 2.0, 16: 2.0, 18: 2.5,
        20: 2.5, 22: 2.5, 24: 3.0, 27: 3.0, 30: 3.5, 36: 4.0,
        42: 4.5, 48: 5.0,
    }
    return table.get(d, 2.0)


def generate_studs():
    """Шпильки ГОСТ 22042-76"""
    rows = []
    for d in [2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 30]:
        for l in [20, 25, 30, 40, 50, 60, 80, 100, 120, 150, 200]:
            if l < d * 2:
                continue
            params = {
                "d": d, "d1": d, "l": l,
                "P_coarse": _pitch(d),
                "execution": 1,
                "tolerance": "6g",
                "strength": "5.8",
                "recommended": d not in [14, 18, 22],
            }
            if d >= 10:
                params["P_fine"] = 1.25
            rows.append({
                "type_name": "Шпилька",
                "name": f"Шпилька М{d}×{l} ГОСТ 22042-76",
                "gost_number": "ГОСТ 22042-76",
                "params": params,
            })
    return rows


def generate_nuts():
    """Гайки ГОСТ 5915-70"""
    key_size = {
        3: 5.5, 4: 7, 5: 8, 6: 10, 8: 13, 10: 16, 12: 18,
        14: 21, 16: 24, 18: 27, 20: 30, 22: 32, 24: 36,
        27: 41, 30: 46, 36: 55, 42: 65, 48: 75,
    }
    height = {
        3: 2.4, 4: 3.2, 5: 4, 6: 5, 8: 6.5, 10: 8, 12: 10,
        14: 11, 16: 13, 18: 15, 20: 16, 22: 18, 24: 19,
        27: 22, 30: 24, 36: 29, 42: 34, 48: 38,
    }
    rows = []
    for d in [3, 4, 5, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 27, 30, 36, 42, 48]:
        rows.append({
            "type_name": "Гайка",
            "name": f"Гайка М{d} ГОСТ 5915-70",
            "gost_number": "ГОСТ 5915-70",
            "params": {
                "d": d, "d1": d,
                "s": key_size.get(d, 75),
                "h": height.get(d, 38),
                "P_coarse": _pitch(d),
                "tolerance": "6H",
                "strength": "5",
                "recommended": d not in [14, 18, 22, 27],
            },
        })
    return rows


def generate_bolts():
    """Болты ГОСТ 7798-70"""
    key_size = {
        6: 10, 8: 13, 10: 16, 12: 18, 14: 21, 16: 24,
        18: 27, 20: 30, 22: 32, 24: 36, 27: 41, 30: 46,
    }
    rows = []
    for d in [6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 27, 30]:
        for l in [20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 120, 150]:
            if l < d * 2:
                continue
            rows.append({
                "type_name": "Болт",
                "name": f"Болт М{d}×{l} ГОСТ 7798-70",
                "gost_number": "ГОСТ 7798-70",
                "params": {
                    "d": d, "d1": d, "l": l,
                    "s": key_size.get(d, 46),
                    "P_coarse": _pitch(d),
                    "tolerance": "6g",
                    "strength": "5.8",
                    "recommended": d not in [14, 18, 22, 27],
                },
            })
    return rows


def generate_screws():
    """Шурупы ГОСТ 1491-80"""
    rows = []
    for d in [2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0]:
        for l in [13, 16, 20, 25, 30, 35, 40, 45, 50, 60]:
            rows.append({
                "type_name": "Шуруп",
                "name": f"Шуруп {d}×{l} ГОСТ 1491-80",
                "gost_number": "ГОСТ 1491-80",
                "params": {
                    "d": d,
                    "d1": round(d * 0.6, 2),
                    "l": l,
                    "P_coarse": (
                        1.0 if d <= 3 else
                        1.5 if d <= 4 else
                        1.75 if d <= 5 else
                        2.0
                    ),
                    "tolerance": "8g",
                    "strength": "—",
                },
            })
    return rows


def init_db() -> None:
    with get_cursor(commit=True) as cur:
        cur.execute(DDL)

        for g in GOSTS_DATA:
            cur.execute(
                """
                INSERT INTO gosts (number, title, year, description, metadata)
                VALUES (%(number)s, %(title)s, %(year)s, %(description)s, %(metadata)s)
                ON CONFLICT (number) DO NOTHING
                """,
                {**g, "metadata": json.dumps(g["metadata"], ensure_ascii=False)},
            )

        cur.execute("SELECT COUNT(*) AS cnt FROM fasteners")
        if cur.fetchone()["cnt"] == 0:
            all_items = (
                generate_studs()
                + generate_nuts()
                + generate_bolts()
                + generate_screws()
            )
            for item in all_items:
                cur.execute(
                    """
                    INSERT INTO fasteners (type_name, name, gost_number, params)
                    VALUES (%(type_name)s, %(name)s, %(gost_number)s, %(params)s)
                    """,
                    {**item, "params": json.dumps(item["params"], ensure_ascii=False)},
                )
            print(f"[init_db] Inserted {len(all_items)} fasteners.")
        else:
            print("[init_db] Already seeded, skipping.")
