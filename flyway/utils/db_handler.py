from flyway.utils.db_base import *


def read_environment(values):
    # parameters for "SELECT"
    table_name = "environment"
    columns = ["*"]
    filters = ["cloud_name"]
    filter_values = [values]

    data = read_record(table_name, columns, filters, values, True)

    if len(data) == 0:
        print('no record found for cloud %s' % filter_values)
        return None

    # should be only one row
    env_data = {'auth_url': data[0][2],
                'by_pass_url': data[0][3],
                'tenant_id': data[0][4],
                'tenant_name': data[0][5],
                'username': data[0][6],
                'password': data[0][7],
                'endpoint': data[0][8],
                'cloud_name': data[0][1]}
    return env_data


def update_environment():
    """function that update the environment config record for both cloud
    """
    table_name = "environment"

    columns = ["cloud_name", "auth_url", "bypass_url",
               "tenant_id","tenant_name", "username", "password",
               "glance_endpoint", "keystone_endpoint"]

    # preparing values for insert or update the environment configs
    d_environment = "'" + cfg.CONF.TARGET.os_cloud_name + "','" \
                    + cfg.CONF.TARGET.os_auth_url + "','" \
                    + cfg.CONF.TARGET.os_bypass_url + "','" \
                    + cfg.CONF.TARGET.os_tenant_id + "','" \
                    + cfg.CONF.TARGET.os_tenant_name + "','" \
                    + cfg.CONF.TARGET.os_username + "','" \
                    + cfg.CONF.TARGET.os_password + "','" \
                    + cfg.CONF.TARGET.os_glance_endpoint + "','" \
                    + cfg.CONF.TARGET.os_keystone_endpoint + "'"

    s_environment = "'" + cfg.CONF.SOURCE.os_cloud_name + "','" \
                    + cfg.CONF.SOURCE.os_auth_url + "','" \
                    + cfg.CONF.SOURCE.os_bypass_url + "','" \
                    + cfg.CONF.SOURCE.os_tenant_id + "','" \
                    + cfg.CONF.SOURCE.os_tenant_name + "','" \
                    + cfg.CONF.SOURCE.os_username + "','" \
                    + cfg.CONF.SOURCE.os_password + "','" \
                    + cfg.CONF.SOURCE.os_glance_endpoint + "','" \
                    + cfg.CONF.SOURCE.os_keystone_endpoint + "'"

    if not check_table_exist(table_name):
        create_environment(s_environment, d_environment)
        return

    update_table(table_name, columns, s_environment, False)
    update_table(table_name, columns, d_environment, True)


def create_environment(s_environment, d_environment):
    # create the environment table
    table_name = "environment"
    columns = "id INT NOT NULL AUTO_INCREMENT, " \
              "cloud_name VARCHAR(32) NOT NULL, " \
              "auth_url VARCHAR(2083) NOT NULL, " \
              "bypass_url VARCHAR(2083), " \
              "tenant_id VARCHAR(128), " \
              "tenant_name VARCHAR(128) NOT NULL, " \
              "username VARCHAR(128) NOT NULL, " \
              "password VARCHAR(512) NOT NULL, " \
              "glance_endpoint VARCHAR(256) NOT NULL, " \
              "keystone_endpoint VARCHAR(256) NOT NULL, " \
              "PRIMARY KEY(id, cloud_name)"

    create_table(table_name, columns, False)

    s_environment = "NULL," + s_environment
    d_environment = "NULL," + d_environment

    insert_record(table_name, s_environment, False)
    insert_record(table_name, d_environment, True)


def config_content(src_config, dst_config):
    config = '[SOURCE]\n'
    config += 'os_auth_url = ' + src_config['auth_url'] + '\n'
    config += 'os_bypass_url = ' + src_config['by_pass_url'] + '\n'
    config += 'os_tenant_id = ' + src_config['tenant_id'] + '\n'
    config += 'os_tenant_name = ' + src_config['tenant_name'] + '\n'
    config += 'os_username = ' + src_config['username'] + '\n'
    config += 'os_password = ' + src_config['password'] + '\n'
    config += 'os_endpoint = ' + src_config['endpoint'] + '\n'
    config += 'os_cloud_name = ' + src_config['cloud_name'] + '\n'
    config += 'os_glance_endpoint = ' + src_config['glance_endpoint'] + '\n'
    config += 'os_keystone_endpoint = ' + src_config['keystone_endpoint'] + \
              '\n'
    config += '\n\n'
    config += '[TARGET]\n'
    config += 'os_auth_url = ' + dst_config['auth_url'] + '\n'
    config += 'os_bypass_url = ' + dst_config['by_pass_url'] + '\n'
    config += 'os_tenant_id = ' + dst_config['tenant_id'] + '\n'
    config += 'os_tenant_name = ' + dst_config['tenant_name'] + '\n'
    config += 'os_username = ' + dst_config['username'] + '\n'
    config += 'os_password = ' + dst_config['password'] + '\n'
    config += 'os_endpoint = ' + dst_config['endpoint'] + '\n'
    config += 'os_cloud_name = ' + dst_config['cloud_name'] + '\n'
    config += 'os_glance_endpoint = ' + dst_config['glance_endpoint'] + '\n'
    config += 'os_keystone_endpoint = ' + dst_config['keystone_endpoint'] + \
              '\n'
    config += '\n\n'
    config += '[DEFAULT]\n'
    config += '# log levels can be CRITICAL, ERROR, WARNING, INFO, DEBUG\n'
    config += 'log_level = DEBUG\n'
    config += 'log_file = /tmp/flyway.log\n'
    config += 'log_format = %(asctime)s %(levelname)s [%(name)s] %(message)s\n'
    return config


def write_to_file(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)


def update_tenant_table():
    """function to create the tenant table
    which is used to record tenant that has
    been migrated
    """

    table_name = "tenant"
    columns = "id INT NOT NULL AUTO_INCREMENT, " \
              "project_name VARCHAR(32) NOT NULL, " \
              "src_uuid VARCHAR(128) NOT NULL, " \
              "src_cloud VARCHAR(128) NOT NULL, " \
              "new_project_name VARCHAR(32) NOT NULL, " \
              "dst_uuid VARCHAR(128) NOT NULL, " \
              "dst_cloud VARCHAR(128) NOT NULL, " \
              "state VARCHAR(128) NOT NULL, " \
              "PRIMARY KEY(id, src_uuid, dst_uuid)"

    if not check_table_exist(table_name):
        create_table(table_name, columns, True)
        return

    delete_all_data(table_name)


def record_tenant_migrated(**tenant_details):
    """function to insert the detail of
    tenant, which has been migrated, into database

    :param tenant_details: relevant data of migrated tenant
    """
    table_name = "tenant"
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
    table_name = "tenant"
    columns = ["*"]
    filters = ["project_name", "cloud_name"]
    filter_values = list(values)

    data = read_record(table_name, columns, filters, values, True)

    if len(data) == 0:
        print('no record found for tenant {0} in cloud {1}'
              .format(filter_values[0], filter_values[1]))
        return None
    elif len(data) > 1:
        print('multiple record found for tenant {0} in cloud {1}'
              .format(filter_values[0], filter_values[1]))
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