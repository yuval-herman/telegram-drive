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
        dir REFERENCES directories(directory))""")

cur.execute(
    """CREATE TABLE IF NOT EXISTS directories(
        directory INTEGER PRIMARY KEY,
        directory_Parent REFERENCES directories(directory),
        owner_id,
        name
        )""")
con.commit()

Directory = Tuple[int, int, int, str]


def insert_file(name: str, telegram_id: str, user_id: int, directory: int | None = None) -> int | None:
    rowid = cur.execute("INSERT INTO files (name,telegram_id,user_id,dir) VALUES(?,?,?,?)",
                        [name, telegram_id, user_id, directory]).lastrowid
    con.commit()
    return rowid


def get_user_files(user_id: int) -> List[Tuple[str, int, int]]:
    return cur.execute("SELECT name, id, dir FROM files WHERE user_id = ?", [user_id]).fetchall()


def get_telegramID_by_id(file_id: int) -> str:
    return cur.execute("SELECT telegram_id FROM files WHERE id = ?", [file_id]).fetchone()[0]


def search_file_for_user(user_id: int, file_name: str) -> List[Tuple[str, int, int]]:
    return cur.execute("""SELECT name, id, dir FROM files
    WHERE user_id = ? AND name LIKE ? AND dir is NOT NULL""", [user_id, f'%{file_name}%']).fetchall()


def get_dir(parent_id: int | None, name: str, user_id: int) -> Directory | None:
    """directory structure is:
    1.directory
    2.directory_Parent
    3.owner_id
    4.name
    """
    return cur.execute(f"""SELECT * FROM directories
    WHERE {"directory_Parent = ?" if parent_id else "directory_Parent is ?"} AND name = ? AND owner_id = ?""", [parent_id, name, user_id]).fetchone()


def get_root_dir_names(user_id: int) -> List[str] | None:
    return [name[0] for name in (cur.execute(f"""SELECT name FROM directories
    WHERE directory_Parent is null AND owner_id = ?""", [user_id]).fetchall() or [])]


def get_dir_names_under_dir(user_id: int, parent_dir: int | None) -> List[str] | None:
    return [name[0] for name in (cur.execute(f"""SELECT name FROM directories
    WHERE directory_Parent = ? AND owner_id = ?""", [parent_dir, user_id]).fetchall() or [])]


def get_dir_full_path(user_id: int, dir_id: int) -> str:
    directory: Directory = cur.execute(
        "select * from directories where owner_id = ? and directory = ?", [user_id, dir_id]).fetchone()
    end_path = f'{directory[3]}/'
    while directory[1]:
        directory: Directory = cur.execute(
            "select * from directories where owner_id = ? and directory = ?", [user_id, directory[1]]).fetchone()
        end_path = f'{directory[3]}/{end_path}'
    return end_path


def change_file_dir(file_id: int, directory_id: int):
    cur.execute("""UPDATE files SET dir = ? WHERE id = ?""",
                [directory_id, file_id])
    con.commit()


def insert_dir(directory_Parent: int | None, owner_id: int, name: str) -> int | None:
    rowid = cur.execute("INSERT INTO directories (directory_Parent,owner_id,name) VALUES(?,?,?)", [
        directory_Parent, owner_id, name]).lastrowid
    con.commit()
    return rowid
