import sqlite3
from typing import List, Tuple, Union
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


def insert_file(name: str, telegram_id: str, user_id: int, directory: Union[int, None] = None) -> int:
    rowid = cur.execute("INSERT INTO files (name,telegram_id,user_id,dir) VALUES(?,?,?,?)",
                        [name, telegram_id, user_id, directory]).lastrowid
    con.commit()
    if rowid is None:
        raise Exception("Database error: couldn't insert file")
    return rowid


def get_user_files(user_id: int) -> List[Tuple[str, int, int]]:
    return cur.execute("SELECT name, id, dir FROM files WHERE user_id = ?", [user_id]).fetchall()


def get_telegramID_by_id(file_id: int) -> str:
    return cur.execute("SELECT telegram_id FROM files WHERE id = ?", [file_id]).fetchone()[0]


def search_file_for_user(user_id: int, file_name: str) -> List[Tuple[str, int, int]]:
    return cur.execute("""SELECT name, id, dir FROM files
    WHERE user_id = ? AND name LIKE ? AND dir is NOT NULL""", [user_id, f'%{file_name}%']).fetchall()


def get_child_dir(parent_id: Union[int, None], name: str, user_id: int) -> Union[Directory, None]:
    return cur.execute(f"""SELECT * FROM directories
    WHERE {"directory_Parent = ?" if parent_id else "directory_Parent is ?"}
    AND name = ? AND owner_id = ?""", [parent_id, name, user_id]).fetchone()


def get_parent_dir(dir_id: int, user_id: int) -> Union[Directory, None]:
    return cur.execute(f"""select * from directories
    where directory = (SELECT directory_Parent FROM directories
    WHERE directory = ? AND owner_id = ?)""", [dir_id, user_id]).fetchone()


def get_root_dir_names(user_id: int) -> Union[List[str], None]:
    return [name[0] for name in (cur.execute(f"""SELECT name FROM directories
    WHERE directory_Parent is null AND owner_id = ?""", [user_id]).fetchall() or [])]


def get_dir_names_under_dir(user_id: int, parent_dir: Union[int, None]) -> List[str]:
    return [name[0]+'/' for name in cur.execute(f"""SELECT name FROM directories
    WHERE {"directory_Parent = ?" if parent_dir else "directory_Parent is ?"}
    AND owner_id = ?""", [parent_dir, user_id]).fetchall()]


def get_file_names_under_dir(user_id: int, dir: Union[int, None]) -> List[str]:
    return [name[0] for name in cur.execute(f"""select name from files 
        where dir = ? AND user_id = ?""", [dir, user_id]).fetchall()]


def get_telegramID_by_name(user_id: int, dir: int, name: str) -> Union[str, None]:
    return cur.execute(f"""select telegram_id from files 
        where dir = ? AND user_id = ? AND name = ?""", [dir, user_id, name]).fetchone()[0]


def get_fileID_by_name(user_id: int, dir: Union[int, None], name: str) -> Union[int, None]:
    return (cur.execute(f"""select id from files 
        where {"dir = ?" if dir else "dir is ?"}
        AND user_id = ? AND name = ?""", [dir, user_id, name]).fetchone() or [None])[0]


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
    cur.execute("UPDATE files SET dir = ? WHERE id = ?",
                [directory_id, file_id])
    con.commit()


def insert_dir(directory_Parent: Union[int, None], owner_id: int, name: str) -> Union[int, None]:
    rowid = cur.execute("INSERT INTO directories (directory_Parent,owner_id,name) VALUES(?,?,?)", [
        directory_Parent, owner_id, name]).lastrowid
    con.commit()
    return rowid


def get_user_top_dirs(user_id: int) -> List[Directory]:
    return cur.execute("SELECT * FROM directories WHERE owner_id = ? AND directory_Parent is NULL", [user_id]).fetchall()


def change_file_name(new_name: str, file_id: int) -> None:
    cur.execute("UPDATE files SET name = ? WHERE id = ?", [new_name, file_id])
    con.commit()


def change_dir_name(new_name: str, dir_id: int) -> None:
    cur.execute("UPDATE directories SET name = ? WHERE directory = ?",
                [new_name, dir_id])
    con.commit()


def change_file_parent(new_parent: int, file_id: int) -> None:
    cur.execute("UPDATE files SET dir = ? WHERE id = ?", [new_parent, file_id])
    con.commit()


def change_dir_parent(new_parent: int, dir_id: int) -> None:
    cur.execute("UPDATE directories SET directory_Parent = ? WHERE directory = ?",
                [new_parent, dir_id])
    con.commit()
