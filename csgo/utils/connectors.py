import sqlite3
import os
from termcolor import colored

def get_db_name(db_name : str) -> str:
    return os.path.join( os.environ.get("DB_PATH") , db_name )

class SQLconnector:

    def __init__(self , db_name : str , cursor : bool = True):
        self.db_name = db_name
        self.cursor = bool(cursor)
        self.conn = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_name)
        return self.conn.cursor() if self.cursor else self.conn

    def __exit__(self , *args):
        self.conn.commit()
        self.conn.close()

def drop_table(db_name : str , table_name : str) -> bool:
    try:
        with SQLconnector(db_name = get_db_name(db_name)) as curs:
            curs.execute(f"DROP TABLE IF EXISTS {table_name.strip()};")
            print(colored(f"Succesfully dropped table {table_name}" , "green"))
            return True
    except Exception as e:
        print(colored(f"Failed to drop table {table_name}", "red"))
        return False

def create_leaderboard_table(db_name : str) -> bool:
    try:
        print(get_db_name(db_name))
        with SQLconnector(db_name = get_db_name(db_name)) as curs:
            curs.execute("""CREATE TABLE IF NOT EXISTS leaderboard (
                            date TEXT,
                            playerId INT NOT NULL,
                            playerRanking INT NOT NULL,
                            playerName TEXT NOT NULL,
                            primaryWeapon TEXT,
                            secondaryWeapon TEXT,
                            kd REAL,
                            kills INT,
                            deaths INT,
                            headshots REAL,
                            winRate REAL,
                            vX INT,
                            rating REAL,
                            PRIMARY KEY(playerId)
                    );""")
            print(colored("Succesfully created leaderboard table!", "green"))
            return True
    except Exception:
        print(colored("Failed to create leaderboard table" , "red"))
        return False

def fetch_leaderboard(db_name : str , page : int = 1):
    try:
        columns = []
        with SQLconnector(db_name = get_db_name(db_name)) as curs:
            offset = (page-1)*500
            curs.execute("PRAGMA table_info(leaderboard);")
            columns = list(map(lambda x : x[1] , curs.fetchall()))
            curs.execute("""SELECT * FROM leaderboard 
                            ORDER BY leaderboard.playerRanking ASC
                            LIMIT 200
                            OFFSET (?);""",
                            [offset])
            leaderboard_rows = []
            for result in curs.fetchall():
                leaderboard_rows.append({key : row for key , row in zip(columns,result)})
            return leaderboard_rows
    except Exception as error_message:
        return error_message

def query_db(db_name : str , table_name : str) -> bool:
    try:
        with SQLconnector(db_name = get_db_name(db_name) , cursor = False) as conn:
            conn.row_factory = sqlite3.Row
            curs = conn.cursor()
            curs.execute(f"SELECT * FROM {table_name.strip()};")
            for idx , row in enumerate(curs.fetchall()):
                if idx == 0:
                    for col in row.keys():
                        print(col , end = ",")
                    print()
                for col in row.keys():
                    print(row[col] , end = ",")
                print()
            return True
    except Exception as error_message:
        print(error_message)
        return False