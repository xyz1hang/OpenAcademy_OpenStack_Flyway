from tests.flow.test_base import TestBase

__author__ = 'chengxue'

from flyway.flow.keypairtask import KeypairMigrationTask
from utils.db_handlers import keypairs as db_handler
from utils.helper import *
from time import localtime, time, strftime


class KeypairTaskTest(TestBase):

    def __init__(self, *args, **kwargs):
        super(KeypairTaskTest, self).__init__(*args, **kwargs)
        self.migration_task = \
            KeypairMigrationTask('keypair_migration_task')

        self.s_cloud_name = cfg.CONF.SOURCE.os_cloud_name
        self.t_cloud_name = cfg.CONF.TARGET.os_cloud_name

        self.s_host = cfg.CONF.SOURCE. \
            os_auth_url.split("http://")[1].split(":")[0]
        self.t_host = cfg.CONF.TARGET. \
            os_auth_url.split("http://")[1].split(":")[0]

    def test_execute(self):
        user_admin_s = db_handler.\
            get_info_from_openstack_db(host=self.s_host,
                                       db_name='keystone',
                                       table_name='user',
                                       columns=['id'],
                                       filters={"name": "admin"})
        user_demo_s = db_handler.\
            get_info_from_openstack_db(host=self.s_host,
                                       db_name='keystone',
                                       table_name='user',
                                       columns=['id'],
                                       filters={"name": "demo"})

        user_admin_t = db_handler.\
            get_info_from_openstack_db(host=self.t_host,
                                       db_name='keystone',
                                       table_name='user',
                                       columns=['id'],
                                       filters={"name": "admin"})
        user_demo_t = db_handler.\
            get_info_from_openstack_db(host=self.t_host,
                                       db_name='keystone',
                                       table_name='user',
                                       columns=['id'],
                                       filters={"name": "demo"})

        keypair_name_1 = "admin_keypair_test"
        fingerprint_1 = "1d_2e_3f_4h"
        user_id_1 = user_admin_s[0][0]
        public_key_1 = "abcde"

        insert_value1 = {'created_at': strftime('%Y-%m-%d %H-%M-%S',
                                                localtime(time())),
                         'name': keypair_name_1,
                         'user_id': user_id_1,
                         'fingerprint': fingerprint_1,
                         'public_key': public_key_1,
                         'deleted': '0'}

        keypair_name_2 = "demo_keypair_test"
        fingerprint_2 = "3e_4f_5g_6h"
        user_id_2 = user_demo_s[0][0]
        public_key_2 = "fghic"

        insert_value2 = {'created_at': strftime('%Y-%m-%d %H-%M-%S',
                                                localtime(time())),
                         'name': keypair_name_2,
                         'user_id': user_id_2,
                         'fingerprint': fingerprint_2,
                         'public_key': public_key_2,
                         'deleted': '0'}

        keypair_name_3 = "admin_keypair_test_2"
        fingerprint_3 = "1d_2e_3f_4h"
        user_id_3 = user_admin_t[0][0]
        public_key_3 = "abcde"

        insert_value3 = {'created_at': strftime('%Y-%m-%d %H-%M-%S',
                                                localtime(time())),
                         'name': keypair_name_3,
                         'user_id': user_id_3,
                         'fingerprint': fingerprint_3,
                         'public_key': public_key_3,
                         'deleted': '0'}

        keypair_name_4 = "admin_keypair_test"
        fingerprint_4 = "1d_2e_3f_4h_different"
        user_id_4 = user_admin_t[0][0]
        public_key_4 = "abcde_different"

        insert_value4 = {'created_at': strftime('%Y-%m-%d %H-%M-%S',
                                                localtime(time())),
                         'name': keypair_name_4,
                         'user_id': user_id_4,
                         'fingerprint': fingerprint_4,
                         'public_key': public_key_4,
                         'deleted': '0'}

        # check 1 - whether a key pair has been migrated successfully
        db_handler.insert_info_to_openstack_db(host=self.s_host,
                                               db_name='nova',
                                               table_name='key_pairs',
                                               values=[insert_value1])

        db_handler.insert_info_to_openstack_db(host=self.s_host,
                                               db_name='nova',
                                               table_name='key_pairs',
                                               values=[insert_value2])

        self.migration_task.execute([fingerprint_1, fingerprint_2])

        value_1 = db_handler.\
            get_info_from_openstack_db(host=self.t_host,
                                       db_name='nova',
                                       table_name='key_pairs',
                                       columns=['user_id'],
                                       filters={"deleted": '0',
                                                "name": keypair_name_1,
                                                "fingerprint":
                                                fingerprint_1})

        self.assertEqual(1, len(value_1))
        self.assertEqual(user_admin_t[0][0], value_1[0][0])

        value_2 = db_handler.\
            get_info_from_openstack_db(host=self.t_host,
                                       db_name='nova',
                                       table_name='key_pairs',
                                       columns=['user_id'],
                                       filters={"deleted": '0',
                                                "name": keypair_name_2,
                                                "fingerprint":
                                                fingerprint_2})

        self.assertEqual(1, len(value_2))
        self.assertEqual(user_demo_t[0][0], value_2[0][0])

        # clear all data created for testing
        where_value1 = [fingerprint_1, '0']
        db_handler.delete_info_from_openstack_db(host=self.s_host,
                                                 db_name="nova",
                                                 table_name="key_pairs",
                                                 where_dict=where_value1)
        db_handler.delete_info_from_openstack_db(host=self.t_host,
                                                 db_name="nova",
                                                 table_name="key_pairs",
                                                 where_dict=where_value1)

        where_value2 = [fingerprint_2, '0']
        db_handler.delete_info_from_openstack_db(host=self.s_host,
                                                 db_name="nova",
                                                 table_name="key_pairs",
                                                 where_dict=where_value2)
        db_handler.delete_info_from_openstack_db(host=self.t_host,
                                                 db_name="nova",
                                                 table_name="key_pairs",
                                                 where_dict=where_value2)

        db_handler.delete_keypairs([fingerprint_1, self.s_cloud_name,
                                    self.t_cloud_name])
        db_handler.delete_keypairs([fingerprint_2, self.s_cloud_name,
                                    self.t_cloud_name])

        # check 2 - deal with duplicated key pair (with same fingerprint)
        db_handler.insert_info_to_openstack_db(host=self.s_host,
                                               db_name='nova',
                                               table_name='key_pairs',
                                               values=[insert_value1])

        db_handler.insert_info_to_openstack_db(host=self.t_host,
                                               db_name='nova',
                                               table_name='key_pairs',
                                               values=[insert_value3])

        self.migration_task.execute([fingerprint_1])

        value_3 = db_handler.\
            get_info_from_openstack_db(host=self.t_host,
                                       db_name='nova',
                                       table_name='key_pairs',
                                       columns=['user_id'],
                                       filters={"deleted": '0',
                                                "name": keypair_name_1,
                                                "fingerprint":
                                                fingerprint_1})

        self.assertEqual(0, len(value_3))

        # clear all data created for testing
        where_value1 = [fingerprint_1, '0']
        db_handler.delete_info_from_openstack_db(host=self.s_host,
                                                 db_name="nova",
                                                 table_name="key_pairs",
                                                 where_dict=where_value1)

        db_handler.delete_info_from_openstack_db(host=self.t_host,
                                                 db_name="nova",
                                                 table_name="key_pairs",
                                                 where_dict=where_value1)

        # check 3 - deal with key pairs (belongs to one user)
        #           with duplicated name
        db_handler.insert_info_to_openstack_db(host=self.s_host,
                                               db_name='nova',
                                               table_name='key_pairs',
                                               values=[insert_value1])

        db_handler.insert_info_to_openstack_db(host=self.t_host,
                                               db_name='nova',
                                               table_name='key_pairs',
                                               values=[insert_value4])

        self.migration_task.execute([fingerprint_1])

        value_4 = db_handler.\
            get_info_from_openstack_db(host=self.t_host,
                                       db_name='nova',
                                       table_name='key_pairs',
                                       columns=['user_id'],
                                       filters={"deleted": '0',
                                                "name": keypair_name_1,
                                                "fingerprint":
                                                fingerprint_1})

        self.assertEqual(0, len(value_4))

        # clear all data created for testing
        where_value1 = [fingerprint_1, '0']
        db_handler.delete_info_from_openstack_db(host=self.s_host,
                                                 db_name="nova",
                                                 table_name="key_pairs",
                                                 where_dict=where_value1)

        where_value2 = [fingerprint_4, '0']
        db_handler.delete_info_from_openstack_db(host=self.t_host,
                                                 db_name="nova",
                                                 table_name="key_pairs",
                                                 where_dict=where_value2)