"""
Interface for interaction with the sqlite3 database
created for storing messages.
"""

import sqlite3

class Database():
    def __init__(self, name):
        self.con = sqlite3.connect(name)

