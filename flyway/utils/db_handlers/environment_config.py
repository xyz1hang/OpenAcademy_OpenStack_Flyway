from collections import OrderedDict
from utils.db_base import *


def initialize_environment():
    create_database('flyway')


def read_environment(*value):
    # parameters for "SELECT"
    table_name = "clouds_info"
    columns = ["*"]
    filters = {'cloud_name': value[0]}

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
        [('cloud_name', cfg.CONF.TARGET.os_cloud_name),
         ('auth_url', cfg.CONF.TARGET.os_auth_url),
         ('tenant_name', cfg.CONF.TARGET.os_tenant_name),
         ('username', cfg.CONF.TARGET.os_username),
         ('password', cfg.CONF.TARGET.os_password)])

    s_set_dict = OrderedDict(
        [('cloud_name', cfg.CONF.SOURCE.os_cloud_name),
         ('auth_url', cfg.CONF.SOURCE.os_auth_url),
         ('tenant_name', cfg.CONF.SOURCE.os_tenant_name),
         ('username', cfg.CONF.SOURCE.os_username),
         ('password', cfg.CONF.SOURCE.os_password)])

    t_where_dict = {'cloud_name': cfg.CONF.TARGET.os_cloud_name}
    s_where_dict = {'cloud_name': cfg.CONF.SOURCE.os_cloud_name}

    if not check_table_exist(table_name):
        create_environment()

    values = []
    if check_record_exist(table_name, t_where_dict):
        update_table(table_name, t_set_dict, t_where_dict, False)
    else:
        values.append(t_set_dict)

    if check_record_exist(table_name, s_where_dict):
        update_table(table_name, s_set_dict, s_where_dict, False)
    else:
        values.append(s_set_dict)

    if len(values) is not 0:
        insert_record(table_name, values, False)


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