from testtools import TestCase

from flow.roletask import RoleMigrationTask
from common import config


class RoleTaskTest(TestCase):
    """Unit test for role migration"""

    def __init__(self, *args, **kwargs):

        super(RoleTaskTest, self).__init__(*args, **kwargs)
        config.parse(['--config-file', '../../etc/flyway.conf'])
        self.migration_task = RoleMigrationTask()

    def test_list_names(self):
        print 'no need to test list name method'

    def test_get_roles_to_move(self):
        new_role_name = "iamnewrole"
        new_role = self.migration_task.ks_source.roles.create(new_role_name)
        roles_to_move = self.migration_task.get_roles_to_move()
        self.assertIn(new_role, roles_to_move)
        self.migration_task.ks_source.roles.delete(new_role)
        for role in self.migration_task.ks_source.roles.list():
            if role.name == "iamnewrole" or role.name == "iamnewrole2":
                self.migration_task.ks_source.roles.delete(role)

    def test_migrate_one_role(self):
        new_role_name = "iamnewrole"
        new_role = self.migration_task.ks_source.roles.create(new_role_name)
        roles_to_move = [new_role]
        self.migration_task.migrate_one_role(roles_to_move[0])
        self.assertIn(new_role_name,
                      self.migration_task.
                      list_names(self.migration_task.ks_target.roles.list()))
        for role in self.migration_task.ks_source.roles.list():
            if role.name == "iamnewrole":
                self.migration_task.ks_source.roles.delete(role)
        for role in self.migration_task.ks_target.roles.list():
            if role.name == "iamnewrole":
                self.migration_task.ks_target.roles.delete(role)

    def test_execute(self):
        new_role_name = "iamnewrole"
        self.migration_task.ks_source.roles.create(new_role_name)
        new_role_name = "iamnewrole2"
        self.migration_task.ks_source.roles.create(new_role_name)

        self.migration_task.execute()
        assert(not self.migration_task.get_roles_to_move())

        for role in self.migration_task.ks_source.roles.list():
            if role.name == "iamnewrole" or role.name == "iamnewrole2":
                self.migration_task.ks_source.roles.delete(role)
        for role in self.migration_task.ks_target.roles.list():
            if role.name == "iamnewrole" or role.name == "iamnewrole2":
                self.migration_task.ks_target.roles.delete(role)
