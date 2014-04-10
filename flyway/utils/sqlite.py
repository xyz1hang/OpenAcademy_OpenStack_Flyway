import sqlite3 as sqlite
import sys

class db_engine(object):
        
        def __init__(self):
                super(db_engine, self).__init__()

        def connect(self):
                return sqlite.connect('db/flyway.db')

        def get_cursor(self, connect):
                return connect.cursor()

        def create_table(self, connect, cur, table_name, columns, close):
                query = 'CREATE TABLE IF NOT EXISTS {0} ({1}) '.format(table_name, columns)
               
                try:
                        cur.execute(query)
                except sqlite.Error, e:
                        print "Error %s:" % e.args[0]
                if close:
                        connect.close()

        def insert_records(self, connect, cur, table_name, values, close):
                query = "INSERT INTO {0} VALUES({1})".format(table_name, values)
                print query
                try:
                        cur.execute(query)
                except sqlite.Error, e:
                        print "Error %s:" % e.args[0]
                if close:
                        connect.close()

        def read_records(self, connect, cur, table_name, close):
                query = 'SELECT * FROM {0} '.format(table_name)
                try:
                        cur.execute(query)
                except sqlite.Error, e:
                        print "Error %s:" % e.args[0]
                if close:
                        connect.close()

        def update_records(self, connect, cur, table_name, value, condition, close):
                query = 'UPDATE {0} SET {1} WHERE {2}'.format(table_name, value, condition)
                print query
                try:
                        cur.execute(query)
                except sqlite.Error, e:
                        print "Error %s:" % e.args[0]
                if close:
                        connect.close()

        def delete_records(self, connect, cur, table_name, close):
                query = 'DELETE FROM {0} '.format(table_name)
               
                try:
                        cur.execute(query)
                except sqlite.Error, e:
                        print "Error %s:" % e.args[0]
                if close:
                        connect.close()

        def check_table(self, con, cur, table_name, close):
                query = "SELECT count(*) FROM sqlite_master WHERE type='table' AND name = '{0}'".format(table_name)
                try:
                        cur.execute(query)
                        result = cur.fetchone()
                        if str(result) == '(0,)':
                                return False
                        else:
                                return True
                except sqlite.Error, e:
                        print "Error %s:" % e.args[0]
                if close:
                        connect.close()

if __name__ == '__main__':
        engine = db_engine()
        con = engine.connect()
        table_columns = '''id INTEGER PRIMARY KEY AUTOINCREMENT,
                           name VARCHAR(64),
                           public_key VARCHAR(1028)
                        '''
                
               
        with con:
                cur = con.cursor()
        #cur.execute("INSERT INTO men VALUES(4,'QSDQSD')")
                engine.create_table(con, cur, 'haha', table_columns, False)
        #values = "null, 'wa'";
        #engine.insert_records(con, 'men', values, False)
        #engine.delete_records(con, 'men', True)
                engine.check_table(con, cur, 'haha', False)
        
        
        





