from tests.utils.db_handlers.test_base import TestBase

__author__ = 'chengxue'

from utils.db_handlers import roles as db_handler
from utils.db_base import *


class RoleDBHandlerTest(TestBase):

    def __init__(self, *args, **kwargs):
        super(RoleDBHandlerTest, self).__init__(*args, **kwargs)

    def test_initialise_roles_mapping(self):
        db_handler.initialise_roles_mapping(["name"])
        self.assertEqual(True, check_table_exist("roles"))

        filters = {"roleName": "name"}
        data = read_record("roles", ["*"], filters, True)
        self.assertEqual(1, len(data))

        table_name = "roles"
        delete_record(table_name, filters)

    def test_existed(self):
        db_handler.initialise_roles_mapping(["name"])
        return_data = db_handler.existed("name")
        self.assertIsNot(None, return_data)

        return_data2 = db_handler.existed("name_new")
        self.assertEqual((), return_data2)

        table_name = "roles"
        filters = {"roleName": "name"}
        delete_record(table_name, filters)

    def test_update_completed(self):
        db_handler.initialise_roles_mapping(["name"])
        db_handler.update_complete("name")

        filters = {"roleName": "name"}
        data = read_record("roles", ["*"], filters, True)

        self.assertIsNot(None, data)
        self.assertEqual("completed", data[0][4])

        table_name = "roles"
        filters = {"roleName": "name"}
        delete_record(table_name, filters)

    def test_update_error(self):
        db_handler.initialise_roles_mapping(["name2"])
        db_handler.update_error("name2")

        filters = {"roleName": "name2"}
        data = read_record("roles", ["*"], filters, True)
        self.assertIsNot(None, data)
        self.assertEqual("error", data[0][4])

        table_name = "roles"
        filters = {"roleName": "name2"}
        delete_record(table_name, filters)

    def test_update_cancel(self):
        db_handler.initialise_roles_mapping(["name3"])
        db_handler.update_cancel("name3")

        filters = {"roleName": "name3"}
        data = read_record("roles", ["*"], filters, True)
        self.assertIsNot(None, data)
        self.assertEqual("cancel", data[0][4])

        table_name = "roles"
        filters = {"roleName": "name3"}
        delete_record(table_name, filters)