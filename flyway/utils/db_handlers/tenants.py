__author__ = 'hydezhang'

from utils.db_base import *
from collections import OrderedDict


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
                     images_migrated INT NOT NULL,
                     quota_updated INT NOT NULL,
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

        # check whether record exists before insert
        where_dict = {'src_uuid': t_details["src_uuid"],
                      'src_cloud': t_details["src_cloud"],
                      'dst_cloud': t_details["dst_cloud"]}

        if not check_record_exist(table_name, where_dict):
            values_to_insert.append(t_details)
        else:
            # do a update instead
            update_migration_record(**t_details)

    insert_record(table_name, values_to_insert, True)


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
        #TODO: not handled properly
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
                   'images_migrated': data[0][7],
                   'quota_updated': data[0][8],
                   'state': data[0][9]}
    return tenant_data


def update_migration_record(**tenant_details):
    """function to update tenant migration record

    :param tenant_details: data used to update tenant migration record
    """
    table_name = "tenants"

    w_dict = OrderedDict([('src_uuid', tenant_details["src_uuid"]),
                          ('src_cloud', tenant_details["src_cloud"]),
                          ('dst_cloud', tenant_details["dst_cloud"])])

    update_table(table_name, tenant_details, w_dict, True)


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