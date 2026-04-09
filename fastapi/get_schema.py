import asyncio, sys, json
sys.path.insert(0, '.')
from app.providers.database_provider import async_session_factory
from sqlalchemy import text

TABLES = ['users', 'categories', 'products', 'markets', 'data_sources',
          'price_records', 'crawl_logs', 'price_alerts', 'alert_logs']

async def get_schema():
    async with async_session_factory() as session:
        result = {}
        for table in TABLES:
            # columns
            cols = await session.execute(text("""
                SELECT column_name, data_type, character_maximum_length,
                       is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema='public' AND table_name=:t
                ORDER BY ordinal_position
            """), {"t": table})
            # primary keys
            pks = await session.execute(text("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_schema='public' AND tc.table_name=:t
                  AND tc.constraint_type='PRIMARY KEY'
            """), {"t": table})
            pk_set = {r[0] for r in pks.fetchall()}
            # foreign keys
            fks = await session.execute(text("""
                SELECT kcu.column_name, ccu.table_name AS foreign_table,
                       ccu.column_name AS foreign_column
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu
                  ON ccu.constraint_name = tc.constraint_name
                WHERE tc.table_schema='public' AND tc.table_name=:t
                  AND tc.constraint_type='FOREIGN KEY'
            """), {"t": table})
            fk_map = {r[0]: (r[1], r[2]) for r in fks.fetchall()}
            # unique
            uqs = await session.execute(text("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_schema='public' AND tc.table_name=:t
                  AND tc.constraint_type='UNIQUE'
            """), {"t": table})
            uq_set = {r[0] for r in uqs.fetchall()}

            columns = []
            for row in cols.fetchall():
                col_name, data_type, char_len, nullable, default = row
                dtype = data_type
                if char_len:
                    dtype += f"({char_len})"
                columns.append({
                    "name": col_name,
                    "type": dtype,
                    "nullable": nullable == "YES",
                    "default": default,
                    "pk": col_name in pk_set,
                    "fk": fk_map.get(col_name),
                    "unique": col_name in uq_set,
                })
            result[table] = columns

        print(json.dumps(result, ensure_ascii=False, indent=2))

asyncio.run(get_schema())
