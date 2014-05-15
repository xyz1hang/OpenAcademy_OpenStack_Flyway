from collections import OrderedDict
from tests.utils.db_handlers.test_base import TestBase

__author__ = 'chengxue'

from utils.db_handlers import images as db_handler
from utils.db_base import *


class ImageDBHandlerTest(TestBase):

    def __init__(self, *args, **kwargs):
        super(ImageDBHandlerTest, self).__init__(*args, **kwargs)

    def test_initialise_image_mapping(self):
        db_handler.initialise_image_mapping()
        self.assertEqual(True, check_table_exist("images"))

    def test_record_images(self):
        db_handler.initialise_image_mapping()
        image_data = {'src_image_name': "name",
                        'src_uuid': "123",
                        'src_owner_uuid': "3",
                        'src_cloud': "cloud1",
                        'dst_image_name': "name",
                        'dst_uuid': "321",
                        'dst_owner_uuid': "2",
                        'dst_cloud': "cloud2",
                        'checksum': "sum12345",
                        'state': "unknown"}
        db_handler.record_image_migrated([image_data])

        filters = {"src_image_name": "name",
                   "src_uuid": "123",
                   "src_cloud": "cloud1",
                   "dst_cloud": "cloud2"}
        data = read_record("images", ["*"], filters, True)
        self.assertEqual(1, len(data))

        table_name = "images"
        w_dict = OrderedDict([('src_image_name', "name"),
                              ('src_uuid', "123"),
                              ('src_owner_uuid', "3"),
                              ('src_cloud', "cloud1"),
                              ('dst_cloud', "cloud2")])

        delete_record(table_name, w_dict)

    def test_get_migrated_image(self):
        db_handler.initialise_image_mapping()
        image_data = {'src_image_name': "name",
                        'src_uuid': "123",
                        'src_owner_uuid': "3",
                        'src_cloud': "cloud1",
                        'dst_image_name': "name",
                        'dst_uuid': "321",
                        'dst_owner_uuid': "2",
                        'dst_cloud': "cloud2",
                        'checksum': "sum12345",
                        'state': "unknown"}
        db_handler.record_image_migrated([image_data])

        filters = {"src_image_name": "name",
                   "src_uuid": "123",
                   "src_cloud": "cloud1",
                   "dst_cloud": "cloud2"}
        return_data = db_handler.get_migrated_image(filters)

        self.assertIsNot(None, return_data)

        table_name = "images"
        w_dict = OrderedDict([('src_image_name', "name"),
                              ('src_uuid', "123"),
                              ('src_owner_uuid', "3"),
                              ('src_cloud', "cloud1"),
                              ('dst_cloud', "cloud2")])

        delete_record(table_name, w_dict)

    def test_update_migration_record(self):
        db_handler.initialise_image_mapping()
        image_data = {'src_image_name': "name",
                        'src_uuid': "123",
                        'src_owner_uuid': "3",
                        'src_cloud': "cloud1",
                        'dst_image_name': "name",
                        'dst_uuid': "321",
                        'dst_owner_uuid': "2",
                        'dst_cloud': "cloud2",
                        'checksum': "sum12345",
                        'state': "unknown"}
        db_handler.record_image_migrated([image_data])

        new_data = {'src_image_name': "name",
                        'src_uuid': "123",
                        'src_owner_uuid': "3",
                        'src_cloud': "cloud1",
                        'dst_image_name': "name",
                        'dst_uuid': "321",
                        'dst_owner_uuid': "2",
                        'dst_cloud': "cloud2",
                        'checksum': "sum12345",
                        'state': "completed"}

        db_handler.update_migration_record(**new_data)
        filters = {"src_image_name": "name",
                   "src_uuid": "123",
                   "src_cloud": "cloud1",
                   "dst_cloud": "cloud2"}
        return_data = db_handler.get_migrated_image(filters)

        self.assertIsNot(None, return_data)
        self.assertEqual("completed", return_data[0]["state"])

        table_name = "images"
        w_dict = OrderedDict([('src_image_name', "name"),
                              ('src_uuid', "123"),
                              ('src_owner_uuid', "3"),
                              ('src_cloud', "cloud1"),
                              ('dst_cloud', "cloud2")])

        delete_record(table_name, w_dict)

    def test_delete_migration_record(self):
        db_handler.initialise_image_mapping()
        image_data = {'src_image_name': "name",
                        'src_uuid': "123",
                        'src_owner_uuid': "3",
                        'src_cloud': "cloud1",
                        'dst_image_name': "name",
                        'dst_uuid': "321",
                        'dst_owner_uuid': "2",
                        'dst_cloud': "cloud2",
                        'checksum': "sum12345",
                        'state': "unknown"}
        db_handler.record_image_migrated([image_data])

        values = ["name", "123", "3", "cloud1", "cloud2"]
        db_handler.delete_migration_record(values)

        filters = {"src_image_name": "name",
                   "src_uuid": "123",
                   "src_cloud": "cloud1",
                   "dst_cloud": "cloud2"}
        return_data = db_handler.get_migrated_image(filters)
        self.assertIs(None, return_data)