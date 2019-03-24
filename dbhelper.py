import sqlite3


class DBHelper:
    def __init__(self, dbname="users.sqlite"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname)
        
    def setup(self):
        print("creating table")
        stmt = "CREATE TABLE IF NOT EXISTS items (currency text, price text, owner text)"
        self.conn.execute(stmt)
        self.conn.commit()

    def add_item(self, cur, price, owner):
        stmt = "INSERT INTO items (currency, price, owner) VALUES (?, ?, ?)"
        args = (cur, price, owner)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def delete_item(self, cur, owner):
        stmt = "DELETE FROM items WHERE currency = (?) AND owner = (?)"
        args = (cur, owner )
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_items(self, owner):
        stmt = "SELECT currency, price FROM items WHERE owner = (?)"
        args = (owner, )
        return [x[0]+": "+x[1] for x in self.conn.execute(stmt, args)]
