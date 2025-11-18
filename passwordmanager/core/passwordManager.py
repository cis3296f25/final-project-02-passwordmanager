import sqlite3
import os
import sys

# Database stuff #################################
DB_FILENAME = "vault.db"

def get_base_path():
    if getattr(sys, 'frozen', False):
        app_path = os.path.dirname(sys.executable)
    else: 
        app_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return app_path

db_path = os.path.join(get_base_path(), DB_FILENAME)
conn = sqlite3.connect(db_path, check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site TEXT,
    username TEXT,
    password BLOB
)
""")
c.execute("""
CREATE TABLE IF NOT EXISTS user_metadata (
    username TEXT PRIMARY KEY,
    wrapped_vmk BLOB NOT NULL,
    salt BLOB NOT NULL,
    kdf TEXT NOT NULL,
    kdf_params TEXT NOT NULL
)
""")
conn.commit()
###################################################################################

# this is optional, but here for completeness
# it addresses the case where the credentials table was created earlier before we had the id column
# it's also aggressively simple: we create a new table with the id field, copy all the data from the old table into the new, drop the old table, and rename the new table to the old table name
def ensure_credentials_id_column():
    c.execute("PRAGMA table_info(credentials)")
    cols = [row[1] for row in c.fetchall()]
    if "id" not in cols:
        c.execute("""
        CREATE TABLE credentials_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site TEXT,
            username TEXT,
            password BLOB
        )
        """)
        c.execute("""
        INSERT INTO credentials_new (site, username, password)
        SELECT site, username, password FROM credentials
        """)
        c.execute("DROP TABLE credentials")
        c.execute("ALTER TABLE credentials_new RENAME TO credentials")
        conn.commit()

ensure_credentials_id_column()
