import sqlite3

con = sqlite3.connect('sql_app.db')
tables = con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", tables)
for t in tables:
    tname = t[0]
    cols = con.execute(f"PRAGMA table_info({tname})").fetchall()
    print(f"\n--- {tname} ---")
    for c in cols:
        print(f"  {c[1]} ({c[2]})")
    rows = con.execute(f"SELECT * FROM {tname}").fetchall()
    print(f"  Rows count: {len(rows)}")
    for r in rows[:5]:
        print("   ", r)
