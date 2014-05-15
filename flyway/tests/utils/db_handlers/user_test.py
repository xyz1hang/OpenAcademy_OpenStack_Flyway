from tests.utils.db_handlers.test_base import TestBase
from utils.helper import get_keystone_source

__author__ = 'chengxue'

from utils.db_handlers import users as db_handler
from utils.db_base import *


class UserDBHandlerTest(TestBase):

    def __init__(self, *args, **kwargs):
        super(UserDBHandlerTest, self).__init__(*args, **kwargs)
        self.ks_source = get_keystone_source()

    def test_initialise_users_mapping(self):
        user_resource = self.ks_source.users\
            .create("name", "abc", "x@abc.com", enabled=True)
        user_resource2 = self.ks_source.users\
            .create("name2", "abcd", "x2@abc.com", enabled=True)
        db_handler.initialise_users_mapping([user_resource, user_resource2],
                                            ["name2"])
        self.assertEqual(True, check_table_exist("users"))

        filters = {"name": "name"}
        data = read_record("users", ["*"], filters, True)
        self.assertEqual(1, len(data))

        filters2 = {"name": "name2"}
        data = read_record("users", ["*"], filters2, True)
        self.assertEqual(0, len(data))

        table_name = "users"
        delete_record(table_name, filters)
        delete_record(table_name, filters2)
        self.ks_source.users.delete(user_resource)
        self.ks_source.users.delete(user_resource2)

    def test_existed_in_db(self):
        user_resource = self.ks_source.users\
            .create("name3", "abc3", "x@abc.com", enabled=True)
        db_handler.initialise_users_mapping([user_resource], [])

        return_data = db_handler.existed_in_db(user_resource)
        self.assertEqual(True, return_data)

        user_resource2 = self.ks_source.users.create("name4", "abc4", "",
                                                     enabled=True)
        return_data2 = db_handler.existed_in_db(user_resource2)
        self.assertEqual(False, return_data2)

        table_name = "users"
        filters = {"name": "name3"}
        delete_record(table_name, filters)

        table_name = "users"
        filters = {"name": "name4"}
        delete_record(table_name, filters)

        self.ks_source.users.delete(user_resource)
        self.ks_source.users.delete(user_resource2)

    def test_set_user_complete(self):
        user_resource = self.ks_source.users\
            .create("name", "abc", "x@abc.com", enabled=True)
        db_handler.initialise_users_mapping([user_resource], [])

        db_handler.set_user_complete(user_resource)

        filters = {"name": "name"}
        data = read_record("users", ["*"], filters, True)

        self.assertIsNot(None, data)
        self.assertEqual("completed", data[0][5])

        table_name = "users"
        filters = {"name": "name"}
        delete_record(table_name, filters)
        self.ks_source.users.delete(user_resource)

    def test_get_migrated_user(self):
        user_resource = self.ks_source.users\
            .create("name", "abc", "x@abc.com", enabled=True)
        db_handler.initialise_users_mapping([user_resource], [])

        values = ["name", "OpenStack1", "OpenStack2"]

        return_data = db_handler.get_migrated_user(values)
        self.assertIsNot(None, return_data)
        self.assertEqual("name", return_data["name"])
        self.assertEqual("x@abc.com", return_data["email"])

        table_name = "users"
        filters = {"name": "name"}
        delete_record(table_name, filters)
        self.ks_source.users.delete(user_resource)

    def test_delete_migrated_users(self):
        user_resource = self.ks_source.users\
            .create("name", "abc", "x@abc.com", enabled=True)
        user_resource2 = self.ks_source.users\
            .create("name2", "abc2", "x2@abc.com", enabled=True)
        db_handler.initialise_users_mapping([user_resource,
                                             user_resource2], [])
        db_handler.set_user_complete(user_resource)

        db_handler.delete_migrated_users()

        filters = {"name": "name"}
        data = read_record("users", ["*"], filters, True)
        self.assertEqual(0, len(data))

        filters = {"name": "name2"}
        data = read_record("users", ["*"], filters, True)
        self.assertEqual(1, len(data))

        filters = {"state": "completed"}
        data = read_record("users", ["*"], filters, True)
        self.assertEqual(0, len(data))

        self.ks_source.users.delete(user_resource)
        self.ks_source.users.delete(user_resource2)
        table_name = "users"
        filters = {"name": "name"}
        delete_record(table_name, filters)
        filters = {"name": "name2"}
        delete_record(table_name, filters)

    def test_delete_all_users_mapping(self):
        user_resource = self.ks_source.users\
            .create("name", "abc", "x@abc.com", enabled=True)
        user_resource2 = self.ks_source.users\
            .create("name2", "abc2", "x2@abc.com", enabled=True)
        db_handler.initialise_users_mapping([user_resource,
                                             user_resource2], [])

        db_handler.delete_all_users_mapping([user_resource])

        filters = {"name": "name"}
        data = read_record("users", ["*"], filters, True)
        self.assertEqual(0, len(data))

        filters = {"name": "name2"}
        data = read_record("users", ["*"], filters, True)
        self.assertEqual(1, len(data))

        self.ks_source.users.delete(user_resource)
        self.ks_source.users.delete(user_resource2)
        table_name = "users"
        filters = {"name": "name"}
        delete_record(table_name, filters)
        filters = {"name": "name2"}
        delete_record(table_name, filters)