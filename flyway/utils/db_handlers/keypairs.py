__author__ = 'chengxue'

import sys
sys.path.append('../')
from utils.db_base import *
from collections import OrderedDict


def initialise_keypairs_mapping():
    """function to create the keypairs table
    which is used to record keypairs that has
    been migrated
    """

    table_name = "keypairs"
    columns = '''id INT NOT NULL AUTO_INCREMENT,
                 name VARCHAR(64) NOT NULL,
                 public_key LONGTEXT NOT NULL,
                 src_uuid VARCHAR(128) NOT NULL,
                 src_cloud VARCHAR(128) NOT NULL,
                 new_name VARCHAR(32) NOT NULL,
                 dst_uuid VARCHAR(128) NOT NULL,
                 dst_cloud VARCHAR(128) NOT NULL,
                 state VARCHAR(128) NOT NULL,
                 PRIMARY KEY(id, src_uuid, dst_uuid)
              '''
    if not check_table_exist(table_name):
        create_table(table_name, columns, True)
        return


def record_keypairs(keypair_details):
    """function to insert the detail of
    keypair, which has been migrated, into database

    :param keypair_details: relevant data of migrated keypair
    """
    table_name = "keypairs"
    values_to_insert = []
    for details in keypair_details:
        value_to_insert = "NULL,'" \
                          + details["name"] + "','" \
                          + details["public_key"] + "','" \
                          + details["src_uuid"] + "','" \
                          + details["src_cloud"] + "','" \
                          + details["new_name"] + "','" \
                          + details["dst_uuid"] + "','" \
                          + details["dst_cloud"] + "','" \
                          + details["state"] + "'"
        values_to_insert.append(value_to_insert)

    insert_record(table_name, values_to_insert, True)


def update_keypairs(**keypair_details):
    """function to update the state of a
    keypair record, which has been migrated, into database

    :param keypair_details: relevant data of migrated keypair
    """
    table_name = "keypairs"
    s_dict = OrderedDict([('dst_uuid', keypair_details["dst_uuid"]),
                          ('state', keypair_details["state"])])
    w_dict = OrderedDict([('name', keypair_details["name"]),
                          ('src_cloud', keypair_details["src_cloud"]),
                          ('dst_cloud', keypair_details["dst_cloud"])])

    update_table(table_name, s_dict, w_dict, True)


def delete_keypairs(values):
    """function to delete a keypair record,
    which has been migrated, into database

    :param keypair_details: relevant data of migrated keypair
    """
    table_name = "keypairs"
    w_dict = OrderedDict([('name', values[0]),
                          ('src_cloud', values[1]),
                          ('dst_cloud', values[2])])

    delete_record(table_name, w_dict)


def get_keypairs(values):
    """function to return detail of keypair migration
    :param values: keypair name and cloud name that used to filter data
    :return: keypair migrate detail
    """
    # parameters for "SELECT"
    table_name = "keypairs"
    columns = ["*"]

    filters = {"src_uuid": values[0],
               "src_cloud": values[1],
               "dst_cloud": values[2]}

    data = read_record(table_name, columns, filters, True)

    if not data or len(data) == 0:
        print("no record found for keypair {0} migration from cloud {1} to could {2}"
              .format(filters['src_uuid'], filters['src_cloud'], filters['dst_cloud']))
        return None
    elif len(data) > 1:
        print("multiple record found for keypair {0} migration from cloud {1} to could {2}"
              .format(filters['src_uuid'], filters['src_cloud'], filters['dst_cloud']))
        return None

    # should be only one row
    keypair_data = {'name': data[0][1],
                    'public_key': data[0][2],
                    'src_uuid': data[0][3],
                    'src_cloud': data[0][4],
                    'new_name': data[0][5],
                    'dst_uuid': data[0][6],
                    'dst_cloud': data[0][7],
                    'state': data[0][8]}
    return keypair_data