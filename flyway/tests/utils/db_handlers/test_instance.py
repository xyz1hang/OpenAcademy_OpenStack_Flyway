from tests.utils.db_handlers.test_base import TestBase

__author__ = 'chengxue'

from utils.db_handlers import instances as db_handler
from utils.db_base import *


class InstanceDBHandlerTest(TestBase):

    def __init__(self, *args, **kwargs):
        super(InstanceDBHandlerTest, self).__init__(*args, **kwargs)

    def test_initialise_vm_mapping(self):
        db_handler.initialise_vm_mapping()
        self.assertEqual(True, check_table_exist("instances"))

    def test_record_vm_migrated(self):
        db_handler.initialise_vm_mapping()
        vm_data = {
                'src_server_name': "name",
                'src_uuid': "123",
                'src_cloud': "cloud1",
                'src_tenant': "tenant",
                'dst_server_name': "server",
                'dst_cloud': "cloud2",
                'dst_uuid': 'NULL',
                'dst_tenant': "server",
                'migration_state': "unknown"}
        db_handler.record_vm_migrated([vm_data])

        filters = {"src_server_name": "name",
                   "src_uuid": "123",
                   "src_cloud": "cloud1",
                   "dst_cloud": "cloud2"}
        data = read_record("instances", ["*"], filters, True)
        self.assertEqual(1, len(data))

        table_name = "instances"
        delete_record(table_name, filters)

    def test_get_migrated_vm(self):
        db_handler.initialise_vm_mapping()
        vm_data = {
                'src_server_name': "name",
                'src_uuid': "123",
                'src_cloud': "cloud1",
                'src_tenant': "tenant",
                'dst_server_name': "server",
                'dst_cloud': "cloud2",
                'dst_uuid': 'NULL',
                'dst_tenant': "server",
                'migration_state': "unknown"}
        db_handler.record_vm_migrated([vm_data])

        filters = {"src_server_name": "name",
                   "src_uuid": "123",
                   "src_cloud": "cloud1",
                   "dst_cloud": "cloud2"}
        return_data = db_handler.get_migrated_vm(**filters)

        self.assertIsNot(None, return_data)

        table_name = "instances"
        delete_record(table_name, filters)

    def test_update_migration_record(self):
        db_handler.initialise_vm_mapping()
        vm_data = {
                'src_server_name': "name",
                'src_uuid': "123",
                'src_cloud': "cloud1",
                'src_tenant': "tenant",
                'dst_server_name': "server",
                'dst_cloud': "cloud2",
                'dst_uuid': 'NULL',
                'dst_tenant': "server",
                'migration_state': "unknown"}
        db_handler.record_vm_migrated([vm_data])

        new_data = {
                'src_server_name': "name",
                'src_uuid': "123",
                'src_cloud': "cloud1",
                'src_tenant': "tenant",
                'dst_server_name': "server",
                'dst_cloud': "cloud2",
                'dst_uuid': 'NULL',
                'dst_tenant': "server",
                'migration_state': "completed"}

        db_handler.update_migration_record(**new_data)
        filters = {"src_server_name": "name",
                   "src_uuid": "123",
                   "src_cloud": "cloud1",
                   "dst_cloud": "cloud2"}
        return_data = db_handler.get_migrated_vm(**filters)

        self.assertIsNot(None, return_data)
        self.assertEqual("completed", return_data[0]["migration_state"])

        table_name = "instances"
        delete_record(table_name, filters)

    def test_delete_migration_record(self):
        db_handler.initialise_vm_mapping()
        vm_data = {
                'src_server_name': "name",
                'src_uuid': "123",
                'src_cloud': "cloud1",
                'src_tenant': "tenant",
                'dst_server_name': "server",
                'dst_cloud': "cloud2",
                'dst_uuid': 'NULL',
                'dst_tenant': "server",
                'migration_state': "unknown"}
        db_handler.record_vm_migrated([vm_data])

        values = ["name", "123", "cloud1", "cloud2"]
        db_handler.delete_migration_record(values)

        filters = {"src_server_name": "name",
                   "src_uuid": "123",
                   "src_cloud": "cloud1",
                   "dst_cloud": "cloud2"}
        return_data = db_handler.get_migrated_vm(**filters)
        self.assertIs(None, return_data)