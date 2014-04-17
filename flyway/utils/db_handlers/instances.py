__author__ = 'hydezhang'

from utils.db_base import *


def initialise_vm_mapping():
    table_name = "instances"

    if not check_table_exist(table_name):
        columns = '''id INT NOT NULL AUTO_INCREMENT,
                 src_server_name VARCHAR(32) NOT NULL,
                 src_uuid VARCHAR(128) NOT NULL,
                 src_cloud VARCHAR(128) NOT NULL,
                 src_tenant VARCHAR(32) NOT NULL,
                 dst_cloud VARCHAR(128) NOT NULL,
                 dst_tenant VARCHAR(128) NOT NULL,
                 server_state VARCHAR(128) NOT NULL,
                 migration_state VARCHAR(128) NOT NULL,
                 PRIMARY KEY(id, src_uuid)
              '''
        create_table(table_name, columns, True)
        return


def record_vm_migrated(**vm_details):
    """function to insert the detail of
    tenant, which has been migrated, into database

    :param tenant_details: relevant data of migrated tenant
    """
    table_name = "tenants"
    values_to_insert = "NULL,'" \
                       + vm_details["src_server_name"] + "','" \
                       + vm_details["src_uuid"] + "','" \
                       + vm_details["src_cloud"] + "','" \
                       + vm_details["src_tenant"] + "','" \
                       + vm_details["dst_cloud"] + "','" \
                       + vm_details["dst_tenant"] + "','" \
                       + vm_details["server_state"] + ",'" \
                       + vm_details["migration_state"] + "'"

    insert_record(table_name, values_to_insert, True)


def get_migrated_vm(*values):
    """function to return detail of vm migration
    :param values: tenant name and cloud name that used to filter data
    :return: vm migrate detail
    """
    # parameters for "SELECT"
    table_name = "instances"
    columns = ["*"]
    filters = {"src_server_name": values[0],
               "src_tenant": values[1],
               "src_cloud": values[2]}

    data = read_record(table_name, columns, filters, True)

    if len(data) == 0:
        print('no migration record found for '
              'instance {0} from tenant {1} in cloud {2}'
              .format(add_quotes(filters.keys()[0]),
                      add_quotes(filters.keys()[1]),
                      add_quotes(filters.keys()[2])))
        return None
    elif len(data) > 1:
        print('multiple migration records found for '
              'instance {0} from tenant {1} in cloud {2}'
              .format(add_quotes(filters.keys()[0]),
                      add_quotes(filters.keys()[1]),
                      add_quotes(filters.keys()[2])))
        return None

    # should be only one row
    vm_data = {'src_server_name': data[0][1],
               'src_uuid': data[0][2],
               'src_cloud': data[0][3],
               'src_tenant': data[0][4],
               'dst_cloud': data[0][5],
               'dst_tenant': data[0][6],
               'server_state': data[0][7],
               'migration_state': data[0][8]}
    return vm_data