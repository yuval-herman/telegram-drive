import sqlite3
con = sqlite3.connect("db.db")
cur = con.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS files(name, id UNIQUE, user_id,
            FOREIGN KEY(user_id) REFERENCES users(id))""")


def insert_file(name: str, file_id: str, user_id: int):
    cur.execute("INSERT INTO files VALUES(?,?,?)", [name, file_id, user_id])
    con.commit()
