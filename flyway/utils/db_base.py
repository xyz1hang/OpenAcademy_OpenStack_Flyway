#import mysql.connector
from oslo.config import cfg

__author__ = 'hydezhang'

import MySQLdb
import base64


def connect():
    # preparing database credentials

    password = cfg.CONF.DATABASE.mysql_password
    db = MySQLdb.connect(host=str(cfg.CONF.DATABASE.host),
                         user=str(cfg.CONF.DATABASE.user),
                         passwd=str(password),
                         db=str(cfg.CONF.DATABASE.db_name))

   #password = cfg.CONF.DATABASE.mysql_password
    #password = base64.b64decode(password)

    return db


def get_cursor(db):
    return db.cursor()


def create_database(db_name):

    db = MySQLdb.connect(host=str(cfg.CONF.DATABASE.host),
                         user=str(cfg.CONF.DATABASE.user),
                         passwd=str(cfg.CONF.DATABASE.mysql_password))

    cursor = get_cursor(db)
    query = 'CREATE DATABASE IF NOT EXISTS {0} '.format(db_name)
    try:
        cursor.execute(query) 
        db.commit()
    except MySQLdb.Error, e:
        print("MySQL error: {}".format(e))
        db.rollback()


def create_table(table_name, columns, close):
    """
    function to create database table
    :param table_name: name of the table to be created
    :param columns: columns of the table
    :param close: flag to indicate whether to close db connection
    """
    # establish connection
    db = connect()
    cursor = get_cursor(db)

    query = "CREATE TABLE IF NOT EXISTS {0} ({1}) ".format(table_name, columns)
    print query
    try:
        cursor.execute(query)
        db.commit()
    except MySQLdb.Error, e:
        print("MySql Connector error: {}".format(e))
        db.rollback()

    if close:
        db.close()


def insert_record(table_name, values, close):
    """
    function to do table insert
    :param table_name: name of the table to be effected
    :param values: values columns
    :param close: flag to indicate whether to close db connection
    """
    # establish connection
    db = connect()
    cursor = get_cursor(db)

    for item in values:
        query = "INSERT INTO {0} VALUES ({1})".format(table_name, item)

        try:
            cursor.execute(query)
            db.commit()
        except MySQLdb.Error, e:
            print("MySql Connector error: {}".format(e))
            db.rollback()

    if close:
        db.close()


def update_table(table_name, set_dict, where_dict, close):
    # establish connection
    """function to do update record in table

    :param table_name: name of the table to be effected
    :param set_dict: set dictionary
    :param where_dict: where dictionary
    :param close: flag to indicate whether to close db connection
    """
    db = connect()
    cursor = get_cursor(db)

    # building "SET" string
    set_str = ''
    for key in set_dict.keys():
        if  key != set_dict.keys()[0]:
            set_str += ', '
        set_str += str(key) + " = '" + str(set_dict[key]) + "'"

    # build "WHERE" string
    filter_str = ''
    for key in where_dict.keys():
        if  key != where_dict.keys()[0]:
            filter_str += ' AND '
        filter_str += str(key) + " = '" + str(where_dict[key]) + "'"

    query = "UPDATE {0} SET {1} WHERE {2}".format(table_name, set_str,filter_str)

    try:
        cursor.execute(query)
        db.commit()
    except MySQLdb.Error, e:
        print("MySql error: {}".format(e))
        db.rollback()

    if close:
        db.close()


def read_record(table_name, columns, where_dict, close):
    """
    function that implements SELECT statement
    :param table_name: name of the table to read data from
    :param close: flag to indicate whether to close db connection
    :param columns: columns from which the data is selected
    :param where_dict: where dictionary
    """
    # establish connection
    db = connect()
    cursor = get_cursor(db)

    # build "WHERE" string
    filter_str = ''
    for key in where_dict.keys():
        if  key != where_dict.keys()[0]:
            filter_str += ' AND '
        filter_str += str(key) + " = '" + str(where_dict[key]) + "'"

    # build columns list
    columns_str = ', '.join(columns)

    if len(where_dict.keys()) > 0:
        query = "SELECT {0} FROM {1} WHERE {2}".format(columns_str, table_name, filter_str)
    else:
        query = "SELECT {0} FROM {1} ".format(columns_str, table_name)

    try:
        cursor.execute(query)
        data = cursor.fetchall()
    except MySQLdb.Error, e:
        print("MySQL error: {}".format(e))
        db.rollback()
        
    if close:
        db.close()

    return data


def delete_all_data(table_name):
    """
    function that delete all data from a table
    """
    # establish connection
    db = connect()
    cursor = get_cursor(db)

    query = "DELETE FROM {0}".format(table_name)
    try:
        cursor.execute(query)
    except MySQLdb.Error, e:
        print("MySQL error: {}".format(e))
        db.rollback()
        
    db.close()


def check_table_exist(table_name):
    """
    function that checks whether a table exists
    """
    # establish connection
    db = connect()
    cursor = get_cursor(db)

    table_name = "'" + table_name + "'"
    query = "SHOW TABLES LIKE {0}".format(table_name)
    result = cursor.execute(query)

    db.close()
    if result:
        return True

    return False

def check_record_exist(table_name, where_dict):
    db = connect()
    cursor = get_cursor(db)

    filter_str = ''
    for key in where_dict.keys():
        if  key != where_dict.keys()[0]:
            filter_str += ' AND '
        filter_str += str(key) + " = '" + str(where_dict[key]) + "'"


    query = "SELECT * FROM {0} WHERE {1}".format(table_name, filter_str)

    result = cursor.execute(query)

    db.close()
    if result:
        return True

    return False


def add_quotes(string):
    return "'" + str(string) +  "'"


if __name__ == '__main__':
    create_database('flyway')
    """columns = '''id INT NOT NULL AUTO_INCREMENT,
                 name VARCHAR(10) NOT NULL,
                 age INT NOT NULL,
                 PRIMARY KEY(id)
              '''
    create_table('test1',columns, False)
    """
    values = [("null, 'wangnan', 26"),
              ("null, 'fuchao',27")
             ]
    insert_record('test1', values, False)

    """
    sets = {'name':'hahaha','age':26}
    filters = {'id':1}
    update_table('test1',sets,filters, False)
    """
    columns = ['*']
    wheres = {}
    print read_record('test1', columns, wheres, False )

    print check_record_exist("test1",{'name':'fuchqsdqsdao'})
