import logging
from utils.db_base import *

TABLE_NAME = 'users'
LOG = logging.getLogger(__name__)


def set_user_complete(user):
    update_table(TABLE_NAME,
                 {'state': 'completed'},
                 {'name': user.name,
                  'src_cloud': cfg.CONF.SOURCE.os_cloud_name,
                  'dst_cloud': cfg.CONF.TARGET.os_cloud_name},
                 False)
    LOG.info("User {0} succeeded to migrate, recorded in database".
             format(user))


def initialise_users_mapping(source_users, target_user_names):
    if not check_table_exist(TABLE_NAME):
        table_columns = '''id INT NOT NULL AUTO_INCREMENT,
                       name VARCHAR(64) NOT NULL,
                       email VARCHAR(64),
                       src_cloud VARCHAR(64) NOT NULL,
                       dst_cloud VARCHAR(64) NOT NULL,
                       state VARCHAR(10) NOT NULL,
                       PRIMARY KEY(id),
                       UNIQUE (name, src_cloud, dst_cloud)
                    '''
        create_table(TABLE_NAME, table_columns, False)

    s_cloud_name = cfg.CONF.SOURCE.os_cloud_name
    t_cloud_name = cfg.CONF.TARGET.os_cloud_name
    init_string = "null, '{0}', '{1}', '" + s_cloud_name + "', '" + \
                  t_cloud_name + "', 'unknown'"
    LOG.debug("init_string: " + init_string)

    init_users = []
    for user in source_users:
        if user.name not in target_user_names and not existed_in_db(user):
            init_users.append(
                init_string.format(user.name, user.email))
            LOG.debug("insert user:")
            LOG.debug(init_string.format(user.name, user.email))

    insert_record(TABLE_NAME, init_users, True)


def existed_in_db(user):
    filters = {
        "name": user.name,
        "src_cloud": cfg.CONF.SOURCE.os_cloud_name,
        "dst_cloud": cfg.CONF.TARGET.os_cloud_name
    }
    data = read_record(TABLE_NAME, ["0"], filters, True)
    return data is not None and len(data) > 0


def delete_migrated_users():
    delete_record(TABLE_NAME, {"src_cloud": cfg.CONF.SOURCE.os_cloud_name,
                               "dst_cloud": cfg.CONF.TARGET.os_cloud_name,
                               "state": "completed"})