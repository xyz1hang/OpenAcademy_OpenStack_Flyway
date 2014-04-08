from testtools import TestCase
import mox
import sys
import os
from flyway.utils.helper import get_clients

sys.path.append('../..')
from flyway.flow.roletask import RoleMigrationTask
from flyway.common import config


class RoleTaskTest(TestCase):
    """Unit test for role migration"""

    def __init__(self, *args, **kwargs):
        super(RoleTaskTest, self).__init__(*args, **kwargs)
        config.parse(['--config-file', '../../etc/flyway.conf'])
        self.migration_task = RoleMigrationTask()

        clients = get_clients()
        self.migration_task.ks_source = clients.get_source()
        self.migration_task.ks_target = clients.get_destination()

        self.mox_factory = mox.Mox()

    def test_execute(self):
        new_role_name = "role_that_should_not_exist"
        new_role = self.migration_task.ks_source.roles.create(new_role_name)

        roles_moved_to_target = self.migration_task.execute()

        target_roles = self.migration_task.ks_target.roles.list()
        self.assertIn(roles_moved_to_target[0], target_roles)

        self.migration_task.ks_source.roles.delete(new_role)
        self.migration_task.ks_target.roles.delete(roles_moved_to_target[0])
