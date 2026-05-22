import sqlite3

conn = sqlite3.connect("baiskeli.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(repairs)")
for row in cursor.fetchall():
    print(row)

conn.close()