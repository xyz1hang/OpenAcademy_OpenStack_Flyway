from collections import OrderedDict

__author__ = 'hydezhang'

from utils.db_base import *


def initialise_vm_mapping():
    table_name = "instances"

    if not check_table_exist(table_name):
        columns = '''id INT NOT NULL AUTO_INCREMENT,
                     src_server_name VARCHAR(128) NOT NULL,
                     src_uuid VARCHAR(128) NOT NULL,
                     src_tenant VARCHAR(128) NOT NULL,
                     src_cloud VARCHAR(128) NOT NULL,
                     dst_server_name VARCHAR(128) NOT NULL,
                     dst_uuid VARCHAR(128) NOT NULL,
                     dst_tenant VARCHAR(128) NOT NULL,
                     dst_cloud VARCHAR(128) NOT NULL,
                     migration_state VARCHAR(128) NOT NULL,
                     PRIMARY KEY(id, src_uuid)
                  '''
        create_table(table_name, columns, True)
        return


def record_vm_migrated(instances_details):
    """function to insert the detail of instances migration

    :param instances_details: relevant data of migrated instance
    """
    table_name = "instances"
    values_to_insert = []
    for vm_detail in instances_details:

        # check whether record exists before insert
        where_dict = {'src_uuid': vm_detail["src_uuid"],
                      'src_cloud': vm_detail["src_cloud"],
                      'dst_cloud': vm_detail["dst_cloud"]}

        if not check_record_exist(table_name, where_dict):
            values_to_insert.append(vm_detail)
        else:
            # do a update instead
            update_migration_record(**vm_detail)

    insert_record(table_name, values_to_insert, True)


def get_migrated_vm(**filters):
    """function to return detail of vm migration
    :param filters: tenant name and cloud name that used to filter data
    :return: vm migrate detail
    """
    # parameters for "SELECT"
    table_name = "instances"
    columns = ["*"]

    data = read_record(table_name, columns, filters, True)

    if not data or len(data) == 0:
        return None

    # convert data returned to dictionaries list
    vm_data = []
    for d in data:
        vm_data.append({'src_server_name': d[1],
                        'src_uuid': d[2],
                        'src_tenant': d[3],
                        'src_cloud': d[4],
                        'dst_server_name': d[5],
                        'dst_uuid': d[6],
                        'dst_tenant': d[7],
                        'dst_cloud': d[8],
                        'migration_state': d[9]})
    return vm_data


def update_migration_record(**instance_details):
    """function to update instance migration record

    :param instance_details: data used to update instance migration record
    """
    table_name = "instances"

    w_dict = OrderedDict([('src_uuid', instance_details["src_uuid"]),
                          ('src_cloud', instance_details["src_cloud"]),
                          ('dst_cloud', instance_details["dst_cloud"])])

    update_table(table_name, instance_details, w_dict, True)


def delete_migration_record(values):
    """function to delete a instance migration record in database

    :param values: relevant data of instance migration record
    which is used to filter data
    """
    table_name = "instances"
    record_filter = {'src_server_name': values[0],
                     'src_uuid': values[1],
                     'src_cloud': values[2],
                     'dst_cloud': values[3]}

    delete_record(table_name, record_filter)