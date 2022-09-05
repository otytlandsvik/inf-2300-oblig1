"""
Interface for interaction with the sqlite3 database
created for storing messages.
"""

import sqlite3

class Database():
    def __init__(self, dbname, tname):
        """
        Connects to database dbname and uses tname
        to run future queries
        """
        self.con = sqlite3.connect(dbname)
        self.cur = self.con.cursor()
        self.tname = tname;

    def get(self):
        """ 
        Run get query on restful API.
        Will obtain all messages in database        
        """
        q = "SELECT * FROM " + self.tname
        self.cur.execute(q)
        return self.cur.fetchall()

    def post(self, msg):
        """ Create new message in database """
        q = "INSERT INTO " + self.tname + " (msg) VALUES (\'" + msg + "\')"
        self.cur.execute(q)
        self.con.commit()
    
    def getid(self, msg):
        """ Get ID of given message """
        q = "SELECT ID FROM " + self.tname + " WHERE msg = \'" + msg + "\' ORDER BY ID"
        self.cur.execute(q)
        return self.cur.fetchall()

    def put(self, id, msg):
        """ Alter existing message """
        q = "UPDATE " + self.tname + " SET msg = \'" + msg + "\' WHERE ID = " + str(id)
        self.cur.execute(q)
        self.con.commit()

    def delete(self, id):
        """ Delete message with given id """
        q = "DELETE FROM " + self.tname + " WHERE ID = " + str(id)
        self.cur.execute(q)
        self.con.commit()


if __name__ == "__main__":
    db = Database("messages.db", "messages")

    # db.post("test")
    # db.put(1, "new message")
    # db.delete(2)
    print(db.getid("test"))
    print(db.get())

