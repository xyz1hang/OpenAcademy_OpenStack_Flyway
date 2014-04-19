from collections import OrderedDict

__author__ = 'hydezhang'

from utils.db_base import *


def initialise_image_mapping():
    table_name = "images"

    if not check_table_exist(table_name):
        columns = '''id INT NOT NULL AUTO_INCREMENT,
                     src_image_name VARCHAR(32) NOT NULL,
                     src_uuid VARCHAR(128) NOT NULL,
                     src_owner_uuid VARCHAR(128) NOT NULL,
                     src_cloud VARCHAR(128) NOT NULL,
                     dst_image_name VARCHAR(32) NOT NULL,
                     dst_uuid VARCHAR(128) NOT NULL,
                     dst_owner_uuid VARCHAR(128) NOT NULL,
                     dst_cloud VARCHAR(128) NOT NULL,
                     checksum VARCHAR(1024) NOT NULL,
                     state VARCHAR(128) NOT NULL,
                     PRIMARY KEY(id, src_uuid)
                  '''
        create_table(table_name, columns, True)
        return

    # clear all data for a new migration task
    delete_all_data(table_name)


def record_image_migrated(image_details):
    """function to insert the detail of
    image, which has been migrated, into database

    :param image_details: relevant data of a list of migrated images
    """
    table_name = "images"
    values_to_insert = []
    for img_details in image_details:
        value_to_insert = "NULL,'" \
                           + img_details["src_image_name"] + "','" \
                           + img_details["src_uuid"] + "','" \
                           + img_details["src_owner_uuid"] + "','" \
                           + img_details["src_cloud"] + "','" \
                           + img_details["dst_image_name"] + "','" \
                           + img_details["dst_uuid"] + "','" \
                           + img_details["dst_owner_uuid"] + "','" \
                           + img_details["dst_cloud"] + "','" \
                           + img_details["checksum"] + "','" \
                           + img_details["state"] + "'"

        # check whether record exists before insert
        where_dict = {'src_uuid': img_details["src_uuid"],
                      'src_cloud': img_details["src_cloud"]}

        if not check_record_exist(table_name, where_dict):
            values_to_insert.append(value_to_insert)
            # do a update instead
            update_migration_record(**img_details)

    insert_record(table_name, values_to_insert, True)


def get_migrated_image(values):
    """function to return detail of image migration
    :param values: image id on source cloud and cloud name that
    used to filter data
    :return: image migrate detail
    """
    # parameters for "SELECT"
    table_name = "images"
    columns = ["*"]
    filters = {"src_image_name": values[0],
               "src_uuid": values[1],
               "src_owner_uuid": values[2] if values[2] else 'NULL',
               "src_cloud": values[3]}

    data = read_record(table_name, columns, filters, True)

    if not data or len(data) == 0:
        print("no migration record found for image {0} "
              "[owned_id: {1}] in cloud {2}"
              .format(add_quotes(values[0]),
                      add_quotes(values[2]),
                      add_quotes(values[3])))
        return None
    elif len(data) > 1:
        print("multiple migration record found for image {0} "
              "[owned_id: {1}] in cloud {2}"
              .format(add_quotes(values[0]),
                      add_quotes(values[2]),
                      add_quotes(values[3])))
        return None

    # should be only one row
    image_data = {'src_image_name': data[0][1],
                  'src_uuid': data[0][2],
                  'src_owner_uuid': data[0][3],
                  'src_cloud': data[0][4],
                  'dst_image_name': data[0][5],
                  'dst_uuid': data[0][6],
                  'dst_owner_uuid': data[0][7],
                  'dst_cloud': data[0][8],
                  'checksum': data[0][9],
                  'state': data[0][10]}
    return image_data


def update_migration_record(**image_details):
    """function to update image migration record

    :param image_details: data used to update image migration record
    """
    table_name = "images"
    s_dict = OrderedDict([('src_image_name', image_details["src_image_name"]),
                          ('src_uuid', image_details["src_uuid"]),
                          ('src_owner_uuid', image_details["src_owner_uuid"]),
                          ('src_cloud', image_details["src_cloud"]),
                          ('dst_image_name', image_details["dst_image_name"]),
                          ('dst_uuid', image_details["dst_uuid"]),
                          ('dst_owner_uuid', image_details["dst_owner_uuid"]),
                          ('dst_cloud', image_details["dst_cloud"]),
                          ('checksum', image_details["checksum"]),
                          ('state', image_details["state"])])

    w_dict = OrderedDict([('src_uuid', image_details["src_uuid"]),
                          ('src_cloud', image_details["src_cloud"]),
                          ('dst_cloud', image_details["dst_cloud"])])

    update_table(table_name, s_dict, w_dict, True)