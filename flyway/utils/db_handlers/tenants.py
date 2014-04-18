__author__ = 'hydezhang'

from utils.db_base import *


def initialise_tenants_mapping():
    """function to create the tenant table
    which is used to record tenant that has
    been migrated
    """

    table_name = "tenants"

    if not check_table_exist(table_name):
        columns = '''id INT NOT NULL AUTO_INCREMENT,
                 project_name VARCHAR(32) NOT NULL,
                 src_uuid VARCHAR(128) NOT NULL,
                 src_cloud VARCHAR(128) NOT NULL,
                 new_project_name VARCHAR(32) NOT NULL,
                 dst_uuid VARCHAR(128) NOT NULL,
                 dst_cloud VARCHAR(128) NOT NULL,
                 image_migrated INT NOT NULL,
                 state VARCHAR(128) NOT NULL,
                 PRIMARY KEY(id, src_uuid, dst_uuid)
              '''
        create_table(table_name, columns, True)
        return


def record_tenant_migrated(tenant_details):
    """function to insert the detail of
    tenant, which has been migrated, into database

    :param tenant_details: relevant data of migrated tenant
    """
    table_name = "tenants"
    values_to_insert = []
    for t_details in tenant_details:
        values_to_insert = "NULL,'" \
                           + t_details["project_name"] + "','" \
                           + t_details["src_uuid"] + "','" \
                           + t_details["src_cloud"] + "','" \
                           + t_details["new_project_name"] + "','" \
                           + t_details["dst_uuid"] + "','" \
                           + t_details["dst_cloud"] + "', " \
                           + t_details["image_migrated"] + ", '" \
                           + t_details["state"] + "'"

    insert_record(table_name, [values_to_insert], True)


def get_migrated_tenant(values):
    """function to return detail of tenant migration
    :param values: tenant name and cloud name that used to filter data
    :return: tenant migrate detail
    """
    # parameters for "SELECT"
    table_name = "tenants"
    columns = ["*"]

    filters = {"project_name": values[0],
               "src_cloud": values[1],
               "dst_cloud": values[2]}

    data = read_record(table_name, columns, filters, True)

    if not data or len(data) == 0:
        print("no migration record found for tenant '{0}' in cloud '{1}'"
              .format(values[0], values[1]))
        return None
    elif len(data) > 1:
        print("multiple migration record found for tenant '{0}' in cloud '{1}'"
              .format(values[0], values[1]))
        return None

    # should be only one row
    tenant_data = {'project_name': data[0][1],
                   'src_uuid': data[0][2],
                   'src_cloud': data[0][3],
                   'new_project_name': data[0][4],
                   'dst_uuid': data[0][5],
                   'dst_cloud': data[0][6],
                   'image_migrated': data[0][7],
                   'state': data[0][8]}
    return tenant_data


def delete_migration_record(values):
    """function to delete a tenant migration record in database

    :param values: relevant data of tenant migration record
    which is used to filter data
    """
    table_name = "tenants"
    record_filter = {'project_name': values[0],
                     'src_uuid': values[1],
                     'src_cloud': values[2],
                     'dst_cloud': values[3]}

    delete_record(table_name, record_filter)