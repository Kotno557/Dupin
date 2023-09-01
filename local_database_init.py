import sqlite3
  
conn = sqlite3.connect('local_database.db')
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE clean_record (
        target_ip TEXT,
        table_name TEXT,
        last_update_time REAL,
        isp TEXT,
        hdm TEXT,
        os TEXT,
        UNIQUE (target_ip, table_name)
    );
""")
conn.commit()

cursor.execute("""
    CREATE TABLE path_record (
        target_ip TEXT PRIMARY KEY,
        path TEXT,
        last_update_time REAL
    );
""")
conn.commit()

cursor.close()
conn.close()