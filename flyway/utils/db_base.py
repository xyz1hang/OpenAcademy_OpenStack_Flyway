import mysql.connector
from oslo.config import cfg

__author__ = 'hydezhang'

import MySQLdb
import base64


def connect():
    # preparing database credentials
    password = ""
    base64.decode(cfg.CONF.DATABASE.mysql_password, password)

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
    for i in range(len(filters)):
        filter_str = filter_str + " AND " \
                     + filters[i] + " = " + "'" + values[i] + "'"

    query = "SELECT {0} FROM {1} WHERE {2}" \
        .format(columns, table_name, filter_str)

    cursor.execute(query)
    data = cursor.fetchall()

    if close:
        db.close()

    return data
