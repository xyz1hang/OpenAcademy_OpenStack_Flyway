import mysql.connector
from oslo.config import cfg

__author__ = 'hydezhang'

import MySQLdb
import base64


def connect():
    # preparing database credentials
    password = cfg.CONF.DATABASE.mysql_password
    password = base64.b64decode(password)

    db = MySQLdb.connect(host=cfg.CONF.DATABASE.host,
                         user=cfg.CONF.DATABASE.user,
                         passwd=password,
                         db=cfg.CONF.DATABASE.db_name)
    return db


def get_cursor(db):
    return db.cursor()


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
    try:
        cursor.execute(query)
        db.commit()
    except mysql.connector.Error as err:
        print("MySql Connector error: {}".format(err))
        db.rollback()

    if close:
        db.close()


def insert_record(table_name, values, close):
    """
    function to do table insert
    :param table_name: name of the table to be effected
    :param values: corresponding values to insert for each columns
    :param close: flag to indicate whether to close db connection
    """
    # establish connection
    db = connect()
    cursor = get_cursor(db)

    query = "INSERT INTO {0} VALUES ({1})".format(table_name, values)
    try:
        cursor.execute(query)
        db.commit()
    except mysql.connector.Error as err:
        print("MySql Connector error: {}".format(err))
        db.rollback()

    if close:
        db.close()


def update_table(table_name, columns, new_values, close):
    # establish connection
    """function to do update record in table

    :param table_name: name of the table to be effected
    :param columns: columns to update
    :param new_values: corresponding new values for each columns
    :param close: flag to indicate whether to close db connection
    """
    db = connect()
    cursor = get_cursor(db)

    # building "SET" string
    set_str = columns[0] + " = " + "'" + new_values[0] + "'"
    for i in range(len(columns) - 1):
        set_str = set_str + ", " + columns[i] + " = " + \
            "'" + new_values[i] + "'"

    query = "UPDATE {0} SET {1}".format(table_name, set_str)

    try:
        cursor.execute(query)
        db.commit()
    except mysql.connector.Error as err:
        print("MySql Connector error: {}".format(err))
        db.rollback()

    if close:
        db.close()


def read_record(table_name, columns, filters, values, close):
    """
    function that implements SELECT statement
    :param table_name: name of the table to read data from
    :param close: flag to indicate whether to close db connection
    :param columns: columns from which the data is selected
    :param filters: name of columns that used to filtering data
    :param values: value for each column that used by filter
    """
    # establish connection
    db = connect()
    cursor = get_cursor(db)

    # TODO: consider put filter string building outside this function
    # TODO: in order to be more flexible (e.g include "OR")
    # building filter string
    filter_str = filters[0] + " = " + "'" + values[0] + "'"
    for i in range(len(filters) - 1):
        filter_str = filter_str + " AND " + filters[i] + " = " + "'" + \
                     values[i] + "'"

    # build columns list
    columns_str = columns[0]
    for i in range(len(columns) - 1):
        columns_str = columns_str + ", " + columns[i]

    query = "SELECT {0} FROM {1} WHERE {2}" \
        .format(columns_str, table_name, filter_str)

    cursor.execute(query)
    data = cursor.fetchall()

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
    cursor.execute(query)

    db.close()


def check_table_exist(table_name):
    """
    function that checks whether a table exists
    """
    # establish connection
    db = connect()
    cursor = get_cursor(db)

    table_name = "'" + table_name + "'"
    query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES " \
            "WHERE TABLE_NAME = {0}".format(table_name)
    result = cursor.execute(query)

    db.close()
    if result:
        return True

    return False