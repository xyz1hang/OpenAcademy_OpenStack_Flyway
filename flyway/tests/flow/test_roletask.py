from testtools import TestCase

from flow.roletask import RoleMigrationTask
from common import config


class RoleTaskTest(TestCase):
    """Unit test for role migration"""

    def __init__(self, *args, **kwargs):

        super(RoleTaskTest, self).__init__(*args, **kwargs)
        config.parse(['--config-file', '../../etc/flyway.conf'])
        self.migration_task = RoleMigrationTask()

    def test_execute(self):

        self.migration_task.init_db()
        new_role_name = "role_that_should_not_exist"
        self.migration_task.ks_source.roles.create(new_role_name)
        moved_roles = self.migration_task.execute()
        self.assertIn(new_role_name, moved_roles)
        assert(not self.migration_task.check())

        for role in self.migration_task.ks_source.roles.list():
            if role.name == "role_that_should_not_exist":
                self.migration_task.ks_source.roles.delete(role)

        for role in self.migration_task.ks_target.roles.list():
            if role.name == "role_that_should_not_exist":
                self.migration_task.ks_target.roles.delete(role)
