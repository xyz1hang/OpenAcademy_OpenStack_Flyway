from collections import OrderedDict
from tests.utils.db_handlers.test_base import TestBase

__author__ = 'chengxue'

from utils.db_handlers import flavors as db_handler
from utils.db_base import *


class FlavourDBHandlerTest(TestBase):

    def __init__(self, *args, **kwargs):
        super(FlavourDBHandlerTest, self).__init__(*args, **kwargs)

    def test_initialise_flavor_mapping(self):
        db_handler.initialise_flavor_mapping()
        self.assertEqual(True, check_table_exist("flavors"))

    def test_record_flavor_migrated(self):
        db_handler.initialise_flavor_mapping()
        flavor_data = {'src_flavor_name': "name",
                        'src_uuid': "123",
                        'src_cloud': "cloud1",
                        'dst_flavor_name': "d_name",
                        'dst_uuid': "234",
                        'dst_cloud': "cloud2",
                        'state': "unknown"}
        db_handler.record_flavor_migrated([flavor_data])

        filters = {"src_flavor_name": "name",
                   "src_uuid": "123",
                   "src_cloud": "cloud1",
                   "dst_cloud": "cloud2"}
        data = read_record("flavors", ["*"], filters, True)
        self.assertEqual(1, len(data))

        table_name = "flavors"
        w_dict = OrderedDict([('src_flavor_name', "name"),
                              ('src_uuid', "123"),
                              ('src_cloud', "cloud1"),
                              ('dst_cloud', "cloud2")])

        delete_record(table_name, w_dict)

    def test_get_migrated_flavor(self):
        db_handler.initialise_flavor_mapping()
        flavor_data = {'src_flavor_name': "name",
                        'src_uuid': "123",
                        'src_cloud': "cloud1",
                        'dst_flavor_name': "d_name",
                        'dst_uuid': "234",
                        'dst_cloud': "cloud2",
                        'state': "unknown"}
        db_handler.record_flavor_migrated([flavor_data])

        values = ["name", "123", "cloud1", "cloud2"]
        return_data = db_handler.get_migrated_flavor(values)

        self.assertIsNot(None, return_data)

        table_name = "flavors"
        w_dict = OrderedDict([('src_flavor_name', "name"),
                              ('src_uuid', "123"),
                              ('src_cloud', "cloud1"),
                              ('dst_cloud', "cloud2")])

        delete_record(table_name, w_dict)

    def test_update_migration_record(self):
        db_handler.initialise_flavor_mapping()
        flavor_data = {'src_flavor_name': "name",
                        'src_uuid': "123",
                        'src_cloud': "cloud1",
                        'dst_flavor_name': "d_name",
                        'dst_uuid': "234",
                        'dst_cloud': "cloud2",
                        'state': "unknown"}
        db_handler.record_flavor_migrated([flavor_data])

        new_data = {'src_flavor_name': "name",
                        'src_uuid': "123",
                        'src_cloud': "cloud1",
                        'dst_flavor_name': "d_name",
                        'dst_uuid': "234",
                        'dst_cloud': "cloud2",
                        'state': "completed"}

        values = ["name", "123", "cloud1", "cloud2"]
        db_handler.update_migration_record(**new_data)
        return_data = db_handler.get_migrated_flavor(values)

        self.assertIsNot(None, return_data)
        self.assertEqual("completed", return_data["state"])

        table_name = "flavors"
        w_dict = OrderedDict([('src_flavor_name', "name"),
                              ('src_uuid', "123"),
                              ('src_cloud', "cloud1"),
                              ('dst_cloud', "cloud2")])

        delete_record(table_name, w_dict)

    def test_delete_migration_record(self):
        db_handler.initialise_flavor_mapping()
        flavor_data = {'src_flavor_name': "name",
                        'src_uuid': "123",
                        'src_cloud': "cloud1",
                        'dst_flavor_name': "d_name",
                        'dst_uuid': "234",
                        'dst_cloud': "cloud2",
                        'state': "unknown"}
        db_handler.record_flavor_migrated([flavor_data])

        values = ["name", "123", "cloud1", "cloud2"]
        db_handler.delete_migration_record(values)

        return_data = db_handler.get_migrated_flavor(values)
        self.assertIs(None, return_data)