# coding=UTF-8
import sqlite3 as sq
import subprocess as sp
import difflib

__all__ = ["Database"]

init_sql = """
begin transaction;
    pragma foreign_keys = on;
    create table Shows(
        show_id integer primary key autoincrement,
        show_name text,
        unique(show_name)
    );
    create table Aliases(
        alias_id integer primary key autoincrement,
        show_id integer,
        alias_name text,
        foreign key(show_id) references Shows(show_id) on delete cascade,
        unique(alias_name)
    );
commit;
"""

def init_db(filename):
    with sq.connect(filename) as con:
        cur = con.cursor()
        cur.executescript(init_sql)

class Database(object):


    def __init__(self, filename):
        self.con = sq.connect(filename)
        # Enforce foreign key support
        self.con.execute(
                    "pragma foreign_keys=on;"
                )

    @property
    def all_shows(self):
        with self.con as con:
            try:
                cur = con.cursor()
                cur.execute(
                    "select show_name from Shows"
                )
                shows = [i[0] for i in cur.fetchall()]
                return(shows)

            except sq.Error as e:
                print("Exception retrieving shows:\n\t-> {}".format(e))
                return(None)

    @property
    def all_aliases(self):
        with self.con as con:
            try:
                cur = con.cursor()
                cur.execute(
                    "select alias_name from Aliases"
                )
                shows = [i[0] for i in cur.fetchall()]
                return(shows)

            except sq.Error as e:
                print("Exception retrieving aliases:\n\t-> {}".format(e))
                return(None)

    def add_show(self, name):
        lname = name.strip().lower()

        with self.con as con:
            try:
                cur = con.cursor()

                cur.execute(
                    "insert into Shows(show_name) values (?);",
                    (lname,)
                )
                show_id = cur.lastrowid
                cur.execute(
                    "insert into Aliases(alias_name, show_id) values (?, ?);",
                    (lname, show_id)
                )
            except sq.Error as e:
                print("Exception adding new show {}:\n\t-> {}".format(name, e))
                print("Rolling back commit.")
                if con:
                    con.rollback()

    def delete_show(self, name):
        lname = name.strip().lower()

        with self.con as con:
            try:
                cur = con.cursor()

                cur.execute(
                    "delete from Shows where show_name=?;",
                    (lname,)
                )
            except sq.Error as e:
                print("Exception deleting show {}:\n\t-> {}".format(name, e))
                print("Rolling back commit.")
                if con:
                    con.rollback()

    def add_alias(self, alias_name, target_name):
        l_alias_name = alias_name.strip().lower()
        l_target_name = target_name.strip().lower()

        with self.con as con:
            try:
                cur = con.cursor()
                tid = self.find_show_id(l_target_name)
                if tid is not None:
                    cur.execute(
                        "insert into Aliases(alias_name, show_id) values (?, ?);" ,
                        (l_alias_name, tid)
                    )
                else:
                    raise(IndexError("Show not found in database"))

            except (IndexError, sq.Error) as e:
                print("Exception aliasing show {} -> {}:\n\t-> {}".format(alias_name, target_name, e))
                print("Rolling back commit.")
                if con:
                    con.rollback()

    def delete_alias(self, name):
        lname = name.strip().lower()

        with self.con as con:
            try:
                cur = con.cursor()

                cur.execute(
                    "delete from Aliases where alias_name=?;",
                    (lname,)
                )
            except sq.Error as e:
                print("Exception deleting alias {}:\n\t-> {}".format(name, e))
                print("Rolling back commit.")
                if con:
                    con.rollback()

    def find_show_id(self, name):
        lname = name.strip().lower()
        with self.con as con:
            try:
                cur = con.cursor()
                cur.execute(
                    "select show_id from Shows where show_name=?",
                    (lname,)
                )
                r = cur.fetchone()
                if r is not None:
                    return(r[0])
                else:
                    return(None)
            except sq.Error as e:
                print("Exception during show id lookup for {}:\n\t-> {}".format(name, e))
                return(None)

    def get_parent(self, name):
        lname = name.strip().lower()
        with self.con as con:
            cur = con.cursor()
            cur.execute(
                "select show_name from Aliases left join Shows using (show_id) where alias_name=?",
                (lname,)
            )
            r = cur.fetchone()
            if r is not None:
                return(r[0])
            else:
                return(None)

    def lookup(self, name):
        lname = name.strip().lower()
        return(self.get_parent(lname))

    def fuzzy_lookup(self, name):
        lname = name.strip().lower()
        m = difflib.get_close_matches(lname, self.all_aliases)
        # Determine unique matches
        s = set([self.get_parent(i) for i in m])
        return(s)
