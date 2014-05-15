from tests.utils.db_handlers.test_base import TestBase

__author__ = 'chengxue'

from utils.db_handlers import tenants as db_handler
from utils.db_base import *


class TenantDBHandlerTest(TestBase):

    def __init__(self, *args, **kwargs):
        super(TenantDBHandlerTest, self).__init__(*args, **kwargs)

    def test_initialise_tenants_mapping(self):
        db_handler.initialise_tenants_mapping()
        self.assertEqual(True, check_table_exist("tenants"))

    def test_record_flavor_migrated(self):
        db_handler.initialise_tenants_mapping()
        tenant_data = {'project_name': "name",
                       'src_uuid': "123",
                       'src_cloud': "cloud1",
                       'new_project_name': "new_name",
                       'dst_uuid': "234",
                       'dst_cloud': "cloud2",
                       'images_migrated': '0',
                       'quota_updated': '0',
                       'state': "unknown"}
        db_handler.record_tenant_migrated([tenant_data])

        filters = {"project_name": "name",
               "src_cloud": "cloud1",
               "dst_cloud": "cloud2"}
        data = read_record("tenants", ["*"], filters, True)
        self.assertEqual(1, len(data))

        table_name = "tenants"
        w_dict = {'project_name': "name",
                'src_uuid': "123",
                'src_cloud': "cloud1",
                'dst_cloud': "cloud2"}

        delete_record(table_name, w_dict)

    def test_get_migrated_tenant(self):
        db_handler.initialise_tenants_mapping()
        tenant_data = {'project_name': "name",
                       'src_uuid': "123",
                       'src_cloud': "cloud1",
                       'new_project_name': "new_name",
                       'dst_uuid': "234",
                       'dst_cloud': "cloud2",
                       'images_migrated': '0',
                       'quota_updated': '0',
                       'state': "unknown"}
        db_handler.record_tenant_migrated([tenant_data])

        values = ["name", "cloud1", "cloud2"]
        return_data = db_handler.get_migrated_tenant(values)

        self.assertIsNot(None, return_data)

        table_name = "tenants"
        w_dict = {'project_name': "name",
                'src_uuid': "123",
                'src_cloud': "cloud1",
                'dst_cloud': "cloud2"}

        delete_record(table_name, w_dict)

    def test_update_migration_record(self):
        db_handler.initialise_tenants_mapping()
        tenant_data = {'project_name': "name",
                       'src_uuid': "123",
                       'src_cloud': "cloud1",
                       'new_project_name': "new_name",
                       'dst_uuid': "234",
                       'dst_cloud': "cloud2",
                       'images_migrated': '0',
                       'quota_updated': '0',
                       'state': "unknown"}
        db_handler.record_tenant_migrated([tenant_data])

        new_data = {'project_name': "name",
                       'src_uuid': "123",
                       'src_cloud': "cloud1",
                       'new_project_name': "new_name",
                       'dst_uuid': "234",
                       'dst_cloud': "cloud2",
                       'images_migrated': '0',
                       'quota_updated': '0',
                       'state': "completed"}

        db_handler.update_migration_record(**new_data)

        values = ["name", "cloud1", "cloud2"]
        return_data = db_handler.get_migrated_tenant(values)

        self.assertIsNot(None, return_data)
        self.assertEqual("completed", return_data["state"])

        table_name = "tenants"
        w_dict = {'project_name': "name",
                'src_uuid': "123",
                'src_cloud': "cloud1",
                'dst_cloud': "cloud2"}

        delete_record(table_name, w_dict)

    def test_delete_migration_record(self):
        db_handler.initialise_tenants_mapping()
        tenant_data = {'project_name': "name",
                       'src_uuid': "123",
                       'src_cloud': "cloud1",
                       'new_project_name': "new_name",
                       'dst_uuid': "234",
                       'dst_cloud': "cloud2",
                       'images_migrated': '0',
                       'quota_updated': '0',
                       'state': "unknown"}
        db_handler.record_tenant_migrated([tenant_data])

        values = ["name", "123", "cloud1", "cloud2"]
        db_handler.delete_migration_record(values)

        values = ["name", "cloud1", "cloud2"]
        return_data = db_handler.get_migrated_tenant(values)
        self.assertIs(None, return_data)