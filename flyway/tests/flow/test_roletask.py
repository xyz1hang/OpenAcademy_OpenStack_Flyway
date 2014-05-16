__author__ = 'tianchen'

from flow.roletask import RoleMigrationTask
from utils.db_base import delete_all_data
from tests.flow.test_base import TestBase


class RoleTaskTest(TestBase):
    """Unit test for role migration"""

    def __init__(self, *args, **kwargs):

        super(RoleTaskTest, self).__init__(*args, **kwargs)
        self.migration_task = RoleMigrationTask()
        self.name_repo = []

    def create_roles(self, ks_client, number=5):
        """
        create several new roles in a cloud
        the role names starts from role0, role1, ...
        :param ks_client: keystone client of the target cloud
        :param number: number of new roles to be created
        """
        base_name = 'role'
        for i in range(number):
            new_name = base_name + str(i)
            ks_client.roles.create(new_name)
            if new_name not in self.name_repo:
                self.name_repo.append(new_name)

    def delete_roles(self, ks_client, number=0):
        """
        delete roles in a cloud created in this test
        the role names starts from role0, role1, ...
        :param ks_client: keystone client of the target cloud
        :param number: number of new roles may be not recorded
        """
        base_name = 'role'
        for i in range(number):
            new_name = base_name + str(i)
            if new_name not in self.name_repo:
                self.name_repo.append(new_name)

        for role in ks_client.roles.list():
            if role.name in self.name_repo:
                ks_client.roles.delete(role)

    def compare_list(self, list1, list2):
        """
        list1 should be exactly same as list2
        otherwise test fail
        :param list1: a list contains only strings
        :param list2: a list contains only strings
        """
        for name in list1:
            self.assertIn(name, list2)
        for name in list2:
            self.assertIn(name, list1)

    def contains_list(self, list1, list2):
        """
        all members in list2 should also be contained in list1
        otherwise fail
        :param list1: a list contains only strings
        :param list2: a list contains only strings
        """
        for name in list2:
            self.assertIn(name, list1)

    def test_get_roles_to_move(self):
        # clean first in case that roles tested already exist
        self.delete_roles(self.migration_task.ks_source, 5)
        self.delete_roles(self.migration_task.ks_target, 5)

        self.name_repo = []
        self.create_roles(self.migration_task.ks_source, 5)
        self.compare_list(self.name_repo,
                          self.migration_task.list_names(
                              self.migration_task.get_roles_to_move()
                          ))
        self.delete_roles(self.migration_task.ks_source)

    def test_list_names(self):
        # clean first in case that roles tested already exist
        self.delete_roles(self.migration_task.ks_source, 5)
        self.delete_roles(self.migration_task.ks_target, 5)

        self.create_roles(self.migration_task.ks_source, 1)
        self.assertIn('role0',
                      self.migration_task.list_names(
                          self.migration_task.get_roles_to_move()))
        self.delete_roles(self.migration_task.ks_source)

    def test_execute(self):

        # Test Case 1:
        # create five new roles in source: role1, role2, .... role5
        # use default execution to migrate all to the target
        # delete all new roles in both cloud after test
        delete_all_data('roles')
        self.delete_roles(self.migration_task.ks_source, 5)
        self.delete_roles(self.migration_task.ks_target, 5)

        self.create_roles(self.migration_task.ks_source, 5)
        self.migration_task.execute(None)
        assert(not self.migration_task.get_roles_to_move())
        self.delete_roles(self.migration_task.ks_source)
        self.delete_roles(self.migration_task.ks_target)
        delete_all_data('roles')

        # Test Case 2:
        # create five new roles in source: role1, role2, .... role5
        # use execution with specified list to migrate role1, 2 and 3
        # delete all new roles in both cloud after test

        self.create_roles(self.migration_task.ks_source, 5)
        roles_to_migrate = ['role0', 'role1', 'role2']
        self.migration_task.execute(roles_to_migrate)
        roles_in_target = self.migration_task.list_names(
            self.migration_task.ks_target.roles.list())
        self.contains_list(roles_in_target, roles_to_migrate)
        self.assertNotIn('role3', roles_in_target)
        self.assertNotIn('role4', roles_in_target)
        delete_all_data('roles')

        # Test Case 3:No roles migrated
        self.migration_task.execute()


