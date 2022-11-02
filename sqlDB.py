import sqlite3
from typing import List, Tuple
con = sqlite3.connect("db.db")
cur = con.cursor()
cur.execute(
    "CREATE TABLE IF NOT EXISTS files(name, id UNIQUE, hash UNIQUE, user_id)")


def insert_file(name: str, file_id: str, file_hash: int, user_id: int) -> None:
    cur.execute("INSERT INTO files VALUES(?,?,?,?)",
                [name, file_id, file_hash, user_id])
    con.commit()


def get_user_files(user_id: int) -> List[Tuple[str, int]]:
    return cur.execute("SELECT name, hash FROM files WHERE user_id = ?", [user_id]).fetchall()


def get_fileID_by_hash(file_hash: int) -> str:
    return cur.execute("SELECT id FROM files WHERE hash = ?", [file_hash]).fetchone()[0]
