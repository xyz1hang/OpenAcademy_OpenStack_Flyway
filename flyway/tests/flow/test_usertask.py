from testtools import TestCase
import mox
import sys
import os
#sys.path.append(os.path.abspath(os.path.dirname(__file__)+'/'+'../..'))
from flyway.utils.helper import get_clients

sys.path.append('../..')
from flyway.flow.usertask import UserMigrationTask
from flyway.common import config


class UserTaskTest(TestCase):
    """Unit test for user migration"""

    def __init__(self, *args, **kwargs):
        super(UserTaskTest, self).__init__(*args, **kwargs)
        config.parse(['--config-file', '../../etc/flyway.conf'])
        self.migration_task = UserMigrationTask()

        clients = get_clients()
        self.migration_task.ks_source = clients.get_source()
        self.migration_task.ks_target = clients.get_destination()
        self.mox_factory = mox.Mox()

    def test_execute(self):
        new_user_name = "user_that_should_not_exist"
        new_user_password = "password"
        new_user = self.migration_task.ks_source.users.create(new_user_name, new_user_password)

        users_moved_to_target = self.migration_task.execute()

        target_users = self.migration_task.ks_target.users.list()
        self.assertIn(users_moved_to_target[0], target_users)

        self.migration_task.ks_source.users.delete(new_user)
        self.migration_task.ks_target.users.delete(users_moved_to_target[0])
