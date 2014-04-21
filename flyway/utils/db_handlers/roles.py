import logging
from utils.db_base import *
from common import config


TABLE_NAME = 'roles'
LOG = logging.getLogger(__name__)


def set_complete(role_name):
    update_table(TABLE_NAME,
                 {'state': 'completed'},
                 {'roleName': role_name,
                  'src_cloud': cfg.CONF.SOURCE.os_cloud_name,
                  'dst_cloud': cfg.CONF.TARGET.os_cloud_name},
                 False)


def set_error(role_name):
    update_table(TABLE_NAME,
                 {'state': 'error'},
                 {'roleName': role_name,
                  'src_cloud': cfg.CONF.SOURCE.os_cloud_name,
                  'dst_cloud': cfg.CONF.TARGET.os_cloud_name},
                 False)


def initialise_roles_mapping(name_of_roles_to_move):
    if not check_table_exist(TABLE_NAME):
        print 'table not exist and create table'
        table_columns = '''id INT NOT NULL AUTO_INCREMENT,
                        roleName VARCHAR(64) NOT NULL,
                        src_cloud VARCHAR(64) NOT NULL,
                        dst_cloud VARCHAR(64) NOT NULL,
                        state VARCHAR(10) NOT NULL,
                        PRIMARY KEY(id),
                        UNIQUE (roleName, src_cloud, dst_cloud)
                        '''
        create_table(TABLE_NAME, table_columns, False)

    s_cloud_name = cfg.CONF.SOURCE.os_cloud_name
    t_cloud_name = cfg.CONF.TARGET.os_cloud_name

    for role in name_of_roles_to_move:
        if not existed(role):
            record = "null, '"+role+"','"+s_cloud_name+"', '"+t_cloud_name+"', 'unknown'"
            insert_record(TABLE_NAME, [record], False)


def existed(role_name):
    filters = {
        "roleName": role_name,
        "src_cloud": cfg.CONF.SOURCE.os_cloud_name,
        "dst_cloud": cfg.CONF.TARGET.os_cloud_name
    }
    data = read_record(TABLE_NAME, ["0"], filters, True)
    return data


if __name__ == '__main__':
    print 'empty roles table'
    LOG.info('make roles table empty')
    config.parse(['--config-file', '../../etc/flyway.conf'])
    namelist = []
    initialise_roles_mapping(namelist)
    delete_all_data(TABLE_NAME)
