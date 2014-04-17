__author__ = 'hydezhang'

from utils.db_base import *


def initialise_image_mapping():
    table_name = "images"

    if not check_table_exist(table_name):
        columns = '''id INT NOT NULL AUTO_INCREMENT,
                 src_image_name VARCHAR(32) NOT NULL,
                 src_uuid VARCHAR(128) NOT NULL,
                 src_owner_tenant VARCHAR(128) NOT NULL,
                 src_cloud VARCHAR(128) NOT NULL,
                 dst_image_name VARCHAR(32) NOT NULL,
                 dst_uuid VARCHAR(128) NOT NULL,
                 dst_owner_tenant VARCHAR(128) NOT NULL,
                 dst_cloud VARCHAR(128) NOT NULL,
                 checksum VARCHAR(1024) NOT NULL
                 state VARCHAR(128) NOT NULL
                 PRIMARY KEY(id, src_uuid)
              '''
        create_table(table_name, columns, True)
        return


def record_image_migrated(**image_details):
    """function to insert the detail of
    image, which has been migrated, into database

    :param image_details: relevant data of a list of migrated images
    """
    table_name = "images"
    values_to_insert = "NULL,'" \
                       + image_details["src_image_name"] + "','" \
                       + image_details["src_uuid"] + "','" \
                       + image_details["src_owner_tenant"] + "','" \
                       + image_details["src_cloud"] + "','" \
                       + image_details["dst_image_name"] + "','" \
                       + image_details["dst_uuid"] + "','" \
                       + image_details["dst_owner_tenant"] + "','" \
                       + image_details["dst_cloud"] + "','" \
                       + image_details["checksum"] + "','" \
                       + image_details["state"] + "'"

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
               "src_owner_tenant": values[2],
               "src_cloud": values[3]}

    data = read_record(table_name, columns, filters, True)

    if not data or len(data) == 0:
        print("no migration record found for image {0} " +
              "from tenant {1} in cloud {2}"
              .format(add_quotes(values[0]),
                      add_quotes(values[2]),
                      add_quotes(values[3])))
        return None
    elif len(data) > 1:
        print("multiple migration records found for for image {0} "
              "from tenant {1} in cloud {2}"
              .format(add_quotes(values[0]),
                      add_quotes(values[2]),
                      add_quotes(values[3])))
        return None

    # should be only one row
    image_data = {'src_flavor_name': data[0][1],
                  'src_uuid': data[0][2],
                  'src_owner_tenant': data[0][3],
                  'src_cloud': data[0][4],
                  'dst_image_name': data[0][5],
                  'dst_flavor_name': data[0][6],
                  'dst_uuid': data[0][7],
                  'dst_owner_tenant': data[0][8],
                  'dst_cloud': data[0][9],
                  'checksum': data[0][10],
                  'state': data[0][11]}
    return image_data