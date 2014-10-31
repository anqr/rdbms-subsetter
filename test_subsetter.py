import os
import unittest
import tempfile
import sqlite3
from subsetter import Db


class OverallTest(unittest.TestCase):
   
    def setUp(self):
        schema = ["CREATE TABLE state (abbrev, name)",
                  """CREATE TABLE city (name, state_abbrev, 
                                        FOREIGN KEY (state_abbrev) 
                                        REFERENCES state(abbrev))""",
                  """CREATE TABLE landmark (name, city,
                                            FOREIGN KEY (city)
                                            REFERENCES city(name))""",
                  """CREATE TABLE zeppelins (name, home_city,
                                             FOREIGN KEY (home_city)
                                             REFERENCES city(name))""", # NULL FKs
                  """CREATE TABLE languages_better_than_python (name)""", # empty table
                  ]
        self.source_db_filename = tempfile.mktemp()
        self.source_db = sqlite3.connect(self.source_db_filename)
        self.source_sqla = "sqlite:///%s" % self.source_db_filename
        self.dest_db_filename = tempfile.mktemp()
        self.dest_db = sqlite3.connect(self.dest_db_filename)
        self.dest_sqla = "sqlite:///%s" % self.dest_db_filename
        for statement in schema:
            self.source_db.execute(statement)
            self.dest_db.execute(statement)
        for params in (('MN', 'Minnesota'), ('OH', 'Ohio'), 
                       ('MA', 'Massachussetts'), ('MI', 'Michigan')):
            self.source_db.execute("INSERT INTO state VALUES (?, ?)", params)
        for params in (('Duluth', 'MN'), ('Dayton', 'OH'), 
                       ('Boston', 'MA'), ('Houghton', 'MI')):
            self.source_db.execute("INSERT INTO city VALUES (?, ?)", params)
        for params in (('Lift Bridge', 'Duluth'), ("Mendelson's", 'Dayton'), 
                       ('Trinity Church', 'Boston'), ('Michigan Tech', 'Houghton')):
            self.source_db.execute("INSERT INTO landmark VALUES (?, ?)", params)
        for params in (('Graf Zeppelin', None), ('USS Los Angeles', None)):
            self.source_db.execute("INSERT INTO zeppelins VALUES (?, ?)", params)
        self.source_db.commit()
        self.dest_db.commit()
    
    def tearDown(self):
        self.source_db.close()
        os.unlink(self.source_db_filename)
        self.dest_db.close()
        os.unlink(self.dest_db_filename)

    def test_parents_kept(self):
        src = Db(self.source_sqla)
        dest = Db(self.dest_sqla)
        src.create_subset_in(dest, 0.25)
        cities = self.dest_db.execute("SELECT * FROM city").fetchall()
        self.assertEqual(len(cities), 1)
        joined = self.dest_db.execute("""SELECT c.name, s.name
                                         FROM city c JOIN state s 
                                                     ON (c.state_abbrev = s.abbrev)""")
        joined = joined.fetchall()
        self.assertEqual(len(joined), 1)
             
    def test_null_foreign_keys(self):
        src = Db(self.source_sqla)
        dest = Db(self.dest_sqla)
        src.create_subset_in(dest, 0.25)
        zeppelins = self.dest_db.execute("SELECT * FROM zeppelins").fetchall()
        self.assertEqual(len(zeppelins), 1)
       