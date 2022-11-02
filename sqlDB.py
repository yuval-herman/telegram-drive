import sqlite3
con = sqlite3.connect("db.db")
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS files(name, id UNIQUE, user_id)")


def insert_file(name: str, file_id: str, user_id: int):
    cur.execute("INSERT INTO files VALUES(?,?,?)", [name, file_id, user_id])
    con.commit()


def get_user_files(user_id: int):
    return cur.execute("SELECT name FROM files WHERE user_id = ?", [user_id]).fetchall()
