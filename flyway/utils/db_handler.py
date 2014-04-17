from collections import OrderedDict
from db_base import *


def initialize_environment():
    create_database('flyway')


def read_environment(value):
    # parameters for "SELECT"
    table_name = "clouds_info"
    columns = ["*"]
    filters = {'cloud_name': value}

    data = read_record(table_name, columns, filters, True)
    print data
    print '*********************************************'

    if len(data) == 0:
        print('no record found for cloud %s' % value)
        return None

    # should be only one row
    env_data = {'cloud_name': data[0][1],
                'auth_url': data[0][2],
                'tenant_name': data[0][3],
                'username': data[0][4],
                'password': data[0][5]
    }
    return env_data


def update_environment():
    """function that update the environment config record for both cloud
    """
    table_name = "clouds_info"

    t_set_dict = OrderedDict(
        [('cloud_name', add_quotes(cfg.CONF.TARGET.os_cloud_name)),
         ('auth_url', add_quotes(cfg.CONF.TARGET.os_auth_url)),
         ('tenant_name', add_quotes(cfg.CONF.TARGET.os_tenant_name)),
         ('username', add_quotes(cfg.CONF.TARGET.os_username)),
         ('password', add_quotes(cfg.CONF.TARGET.os_password))])

    s_set_dict = OrderedDict(
        [('cloud_name', add_quotes(cfg.CONF.SOURCE.os_cloud_name)),
         ('auth_url', add_quotes(cfg.CONF.SOURCE.os_auth_url)),
         ('tenant_name', add_quotes(cfg.CONF.SOURCE.os_tenant_name)),
         ('username', add_quotes(cfg.CONF.SOURCE.os_username)),
         ('password', add_quotes(cfg.CONF.SOURCE.os_password))])

    t_where_dict = {'cloud_name': cfg.CONF.TARGET.os_cloud_name}
    s_where_dict = {'cloud_name': cfg.CONF.SOURCE.os_cloud_name}

    if not check_table_exist(table_name):
        create_environment()

    columns = []
    if not check_record_exist(table_name, t_where_dict):
        t_columns = "NULL,"
        t_columns += ", ".join(t_set_dict.values())
        columns.append(t_columns)

    if not check_record_exist(table_name, s_where_dict):
        s_columns = "NULL,"
        s_columns += ", ".join(s_set_dict.values())
        columns.append(s_columns)

    if len(columns) is not 0:
        insert_record(table_name, columns, False)


def create_environment():
    # create the environment table
    table_name = "clouds_info"
    columns = '''id INT NOT NULL AUTO_INCREMENT,
                 cloud_name VARCHAR(32) NOT NULL,
                 auth_url VARCHAR(512) NOT NULL,
                 tenant_name VARCHAR(128) NOT NULL,
                 username VARCHAR(128) NOT NULL,
                 password VARCHAR(512) NOT NULL,
                 UNIQUE (cloud_name),
                 PRIMARY KEY(id)
              '''

    create_table(table_name, columns, False)


def config_content(src_config, dst_config):
    config = '[SOURCE]\n'
    config += 'os_auth_url = ' + src_config['auth_url'] + '\n'
    config += 'os_tenant_name = ' + src_config['tenant_name'] + '\n'
    config += 'os_username = ' + src_config['username'] + '\n'
    config += 'os_password = ' + src_config['password'] + '\n'
    config += 'os_cloud_name = ' + src_config['cloud_name'] + '\n'

    config += '\n\n'

    config += '[TARGET]\n'
    config += 'os_auth_url = ' + dst_config['auth_url'] + '\n'
    config += 'os_tenant_name = ' + dst_config['tenant_name'] + '\n'
    config += 'os_username = ' + dst_config['username'] + '\n'
    config += 'os_password = ' + dst_config['password'] + '\n'
    config += 'os_cloud_name = ' + dst_config['cloud_name'] + '\n'

    config += '\n\n'

    config += '[DEFAULT]\n'
    config += '# log levels can be CRITICAL, ERROR, WARNING, INFO, DEBUG\n'
    config += 'log_level = DEBUG\n'
    config += 'log_file = /tmp/flyway.log\n'
    config += 'log_format = %(asctime)s %(levelname)s [%(name)s] %(message)s\n'

    config += '\n\n'
    config += '[DATABASE]\n'
    config += 'host = localhost\n'
    config += 'user = root\n'
    config += 'mysql_password = cGFzc3dvcmQ=\n'
    config += 'db_name = flyway\n'

    return config


def write_to_file(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)


def initialise_tenants_mapping():
    """function to create the tenant table
    which is used to record tenant that has
    been migrated
    """

    table_name = "tenants"
    columns = '''id INT NOT NULL AUTO_INCREMENT,
                 project_name VARCHAR(32) NOT NULL,
                 src_uuid VARCHAR(128) NOT NULL,
                 src_cloud VARCHAR(128) NOT NULL,
                 new_project_name VARCHAR(32) NOT NULL,
                 dst_uuid VARCHAR(128) NOT NULL,
                 dst_cloud VARCHAR(128) NOT NULL,
                 state VARCHAR(128) NOT NULL,
                 PRIMARY KEY(id, src_uuid, dst_uuid)
              '''
    if not check_table_exist(table_name):
        create_table(table_name, columns, True)
        return


def record_tenant_migrated(**tenant_details):
    """function to insert the detail of
    tenant, which has been migrated, into database

    :param tenant_details: relevant data of migrated tenant
    """
    table_name = "tenants"
    values_to_insert = "NULL,'" \
                       + tenant_details["project_name"] + "','" \
                       + tenant_details["src_uuid"] + "','" \
                       + tenant_details["src_cloud"] + "','" \
                       + tenant_details["new_project_name"] + "','" \
                       + tenant_details["dst_uuid"] + "','" \
                       + tenant_details["dst_cloud"] + "','" \
                       + tenant_details["state"] + "'"

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
               "src_cloud": values[1]}

    data = read_record(table_name, columns, filters, True)

    if len(data) == 0:
        print('no record found for tenant {0} in cloud {1}'
              .format(filters.keys()[0], filters.keys()[1]))
        return None
    elif len(data) > 1:
        print('multiple record found for tenant {0} in cloud {1}'
              .format(filters.keys()[0], filters.keys()[1]))
        return None

    # should be only one row
    tenant_data = {'project_name': data[0][1],
                   'src_uuid': data[0][2],
                   'src_cloud': data[0][3],
                   'new_project_name': data[0][4],
                   'dst_uuid': data[0][5],
                   'dst_cloud': data[0][6],
                   'state': data[0][7]}
    return tenant_data


def initialise_vm_mapping():
    table_name = "instances"
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
    if not check_table_exist(table_name):
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


def get_migrated_vm(values):
    """function to return detail of vm migration
    :param values: tenant name and cloud name that used to filter data
    :return: vm migrate detail
    """
    # parameters for "SELECT"
    table_name = "instances"
    columns = ["*"]
    filters = {"src_server_name": values[0],
               "src_tenant": values[1],
               "cloud_name": values[2]}

    data = read_record(table_name, columns, filters, True)

    if len(data) == 0:
        print('no record found for instance {0} from tenant {1} in cloud {2}'
              .format(add_quotes(filters.keys()[0]),
                      add_quotes(filters.keys()[1]),
                      add_quotes(filters.keys()[2])))
        return None
    elif len(data) > 1:
        print('multiple records found for instance {0} from tenant {1}'
              ' in cloud {2}'.format(add_quotes(filters.keys()[0]),
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


def initialise_flavor_mapping():
    table_name = "flavors"
    columns = '''id INT NOT NULL AUTO_INCREMENT,
                 src_flavor_name VARCHAR(32) NOT NULL,
                 src_uuid VARCHAR(128) NOT NULL,
                 src_cloud VARCHAR(128) NOT NULL,
                 dst_flavor_name VARCHAR(32) NOT NULL,
                 dst_uuid VARCHAR(128) NOT NULL,
                 dst_cloud VARCHAR(128) NOT NULL
                 PRIMARY KEY(id, src_uuid)
              '''
    if not check_table_exist(table_name):
        create_table(table_name, columns, True)
        return


def record_flavor_migrated(**flavor_details):
    """function to insert the detail of
    flavor, which has been migrated, into database

    :param flavor_details: relevant data of migrated flavor
    """
    table_name = "flavors"
    values_to_insert = "NULL,'" \
                       + flavor_details["src_flavor_name"] + "','" \
                       + flavor_details["src_uuid"] + "','" \
                       + flavor_details["src_cloud"] + "','" \
                       + flavor_details["dst_flavor_name"] + "','" \
                       + flavor_details["dst_uuid"] + "','" \
                       + flavor_details["dst_cloud"] + "'"

    insert_record(table_name, values_to_insert, True)


def get_migrated_flavor(values):
    """function to return detail of flavor migration
    :param values: flavor id on source cloud and cloud name that
    used to filter data
    :return: flavor migrate detail
    """
    # parameters for "SELECT"
    table_name = "flavors"
    columns = ["*"]
    filters = {"src_flavor_name": values[0],
               "src_uuid": values[1],
               "src_cloud": values[2]}

    data = read_record(table_name, columns, filters, True)

    if len(data) == 0:
        print('no record found for flavor {0} in cloud {1}'
              .format(add_quotes(filters.keys()[0]),
                      add_quotes(filters.keys()[2])))
        return None
    elif len(data) > 1:
        print('multiple records found for flavor {0} from in cloud {1}'
              .format(add_quotes(filters.keys()[0]),
                      add_quotes(filters.keys()[2])))
        return None

    # should be only one row
    vm_data = {'src_flavor_name': data[0][1],
               'src_uuid': data[0][2],
               'src_cloud': data[0][3],
               'dst_flavor_name': data[0][4],
               'dst_uuid': data[0][5],
               'dst_cloud': data[0][6]}
    return vm_data


def add_quotes(string):
    return "'" + str(string) + "'"