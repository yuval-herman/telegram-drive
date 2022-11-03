import sqlite3
from typing import List, Tuple
con = sqlite3.connect("db.db")
cur = con.cursor()
cur.execute(
    """CREATE TABLE IF NOT EXISTS files(
        id INTEGER PRIMARY KEY,
        name,
        telegram_id UNIQUE,
        user_id,
        dir)""")

cur.execute(
    """CREATE TABLE IF NOT EXISTS directories (
        directory INTEGER PRIMARY KEY, 
        directory_Parent REFERENCES directories(directory),
        owner_id,
        name
        )""")


def insert_file(name: str, telegram_id: str, user_id: int, directory: int | None = None) -> None:
    cur.execute("INSERT INTO files (name,telegram_id,user_id,dir) VALUES(?,?,?,?)",
                [name, telegram_id, user_id, directory])
    con.commit()


def get_user_files(user_id: int) -> List[Tuple[str, int]]:
    return cur.execute("SELECT name, id FROM files WHERE user_id = ?", [user_id]).fetchall()


def get_telegramID_by_id(file_id: int) -> str:
    return cur.execute("SELECT telegram_id FROM files WHERE id = ?", [file_id]).fetchone()[0]


def search_file_for_user(user_id: int, file_name: str) -> List[Tuple[str, int]]:
    return cur.execute("""SELECT name, id FROM files
    WHERE user_id = ? AND name LIKE ?""", [user_id, f'%{file_name}%']).fetchall()
