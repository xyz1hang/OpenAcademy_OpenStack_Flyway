from collections import OrderedDict
from tests.utils.db_handlers.test_base import TestBase
from utils.helper import get_nova_source

__author__ = 'chengxue'

from utils.db_handlers import keypairs as db_handler
from utils.db_base import *


class KeypairDBHandlerTest(TestBase):

    def __init__(self, *args, **kwargs):
        super(KeypairDBHandlerTest, self).__init__(*args, **kwargs)
        self.nv_source = get_nova_source()

        self.s_host = cfg.CONF.SOURCE. \
            os_auth_url.split("http://")[1].split(":")[0]

    def test_initialise_keypairs_mapping(self):
        # test function initialise_keypairs_mapping
        db_handler.initialise_keypairs_mapping()
        self.assertEqual(True, check_table_exist("keypairs"))

    def test_record_keypairs(self):
        # test function record_keypairs
        db_handler.initialise_keypairs_mapping()
        keypair_data = {'name': "keypair_name",
                        'public_key': "public_key",
                        'fingerprint': "fingerprint",
                        'user_name': "user_name",
                        'src_cloud': "cloud1",
                        'dst_cloud': "cloud2",
                        'state': "unknown",
                        'user_id_updated': "0",
                        'new_name': None}
        db_handler.record_keypairs([keypair_data])

        filters = {"fingerprint": "fingerprint",
                   "src_cloud": "cloud1",
                   "dst_cloud": "cloud2"}
        data = read_record("keypairs", ["*"], filters, True)
        self.assertEqual(1, len(data))

        table_name = "keypairs"
        w_dict = OrderedDict([('fingerprint', "fingerprint"),
                              ('src_cloud', "cloud1"),
                              ('dst_cloud', "cloud2")])

        delete_record(table_name, w_dict)

    def test_get_keypairs(self):
        # test function get_keypairs
        db_handler.initialise_keypairs_mapping()
        keypair_data = {'name': "keypair_name",
                        'public_key': "public_key",
                        'fingerprint': "fingerprint",
                        'user_name': "user_name",
                        'src_cloud': "cloud1",
                        'dst_cloud': "cloud2",
                        'state': "unknown",
                        'user_id_updated': 0L,
                        'new_name': None}

        db_handler.record_keypairs([keypair_data])
        values = ["fingerprint", "cloud1", "cloud2"]
        return_data = db_handler.get_keypairs(values)

        self.assertIsNot(None, return_data)

        table_name = "keypairs"
        w_dict = OrderedDict([('fingerprint', "fingerprint"),
                              ('src_cloud', "cloud1"),
                              ('dst_cloud', "cloud2")])

        delete_record(table_name, w_dict)

    def test_update_keypairs(self):
        # test function update_keypairs
        db_handler.initialise_keypairs_mapping()
        keypair_data = {'name': "keypair_name",
                        'public_key': "public_key",
                        'fingerprint': "fingerprint",
                        'user_name': "user_name",
                        'src_cloud': "cloud1",
                        'dst_cloud': "cloud2",
                        'state': "unknown",
                        'user_id_updated': "0",
                        'new_name': None}

        db_handler.record_keypairs([keypair_data])

        new_data = {'name': "keypair_name",
                    'public_key': "public_key",
                    'fingerprint': "fingerprint",
                    'user_name': "user_name",
                    'src_cloud': "cloud1",
                    'dst_cloud': "cloud2",
                    'state': "completed",
                    'user_id_updated': "1",
                    'new_name': None}

        values = ["fingerprint", "cloud1", "cloud2"]
        db_handler.update_keypairs(**new_data)
        return_data = db_handler.get_keypairs(values)

        self.assertIsNot(None, return_data)
        self.assertEqual(1, return_data["user_id_updated"])
        self.assertEqual("completed", return_data["state"])

        table_name = "keypairs"
        w_dict = OrderedDict([('fingerprint', "fingerprint"),
                              ('src_cloud', "cloud1"),
                              ('dst_cloud', "cloud2")])

        delete_record(table_name, w_dict)

    def test_delete_keypairs(self):
        # test function delete_keypairs
        db_handler.initialise_keypairs_mapping()
        keypair_data = {'name': "keypair_name",
                        'public_key': "public_key",
                        'fingerprint': "fingerprint",
                        'user_name': "user_name",
                        'src_cloud': "cloud1",
                        'dst_cloud': "cloud2",
                        'state': "unknown",
                        'user_id_updated': "0",
                        'new_name': None}

        db_handler.record_keypairs([keypair_data])

        values = ["fingerprint", "cloud1", "cloud2"]
        db_handler.delete_keypairs(values)

        return_data = db_handler.get_keypairs(values)
        self.assertIs(None, return_data)

    def test_get_info_from_openstack_db(self):
        key_resource = self.nv_source.keypairs.create(name="name")
        return_data = db_handler.\
            get_info_from_openstack_db(table_name="key_pairs",
                                       db_name='nova',
                                       host=self.s_host,
                                       columns=['name'],
                                       filters={"deleted": '0',
                                                "name": 'name'})
        self.assertEqual(1, len(return_data))
        self.nv_source.keypairs.delete(key_resource)

    def test_delete_info_from_openstack_db(self):
        key = self.nv_source.keypairs.create(name="name")
        db_handler.delete_info_from_openstack_db(host=self.s_host,
                                                 db_name='nova',
                                                 table_name='key_pairs',
                                                 where_dict=[key.fingerprint, 0])

        return_data = db_handler.\
            get_info_from_openstack_db(table_name="key_pairs",
                                       db_name='nova',
                                       host=self.s_host,
                                       columns=['name'],
                                       filters={"deleted": '0',
                                                "name": 'name'})
        self.assertEqual(0, len(return_data))

    def test_insert_info_to_openstack_db(self):
        insert_values = {'created_at': "12-12-12",
                         'name': "name",
                         'user_id': "123",
                         'fingerprint': "fingerprint",
                         'public_key': "public_key",
                         'deleted': '0'}
        db_handler.insert_info_to_openstack_db(host=self.s_host,
                                               db_name='nova',
                                               table_name='key_pairs',
                                               values=[insert_values])

        return_data = db_handler.\
            get_info_from_openstack_db(table_name="key_pairs",
                                       db_name='nova',
                                       host=self.s_host,
                                       columns=['name'],
                                       filters={"deleted": '0',
                                                "user_id": "123",
                                                "fingerprint": 'fingerprint'})
        self.assertEqual(1, len(return_data))
        self.assertEqual("name", return_data[0][0])

        db_handler.delete_info_from_openstack_db(host=self.s_host,
                                                 db_name='nova',
                                                 table_name='key_pairs',
                                                 where_dict=["fingerprint", 0])