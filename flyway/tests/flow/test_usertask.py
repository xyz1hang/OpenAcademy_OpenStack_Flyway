import mox

from flow.usertask import UserMigrationTask
from common import config as cfg
from tests.flow.test_base import TestBase


class UserTaskTest(TestBase):
    """Unit test for user migration"""

    def __init__(self, *args, **kwargs):
        super(UserTaskTest, self).__init__(*args, **kwargs)
        cfg.parse(['--config-file', '../../etc/flyway.conf'])
        self.migration_task = UserMigrationTask()
        self.mox_factory = mox.Mox()

    def test_execute(self):
        new_user_name = "user_that_should_not_exist2"
        new_user_password = "password"
        new_user_email = "liang.shang13@imperial.ac.uk"

        try:
            new_user = self.migration_task.ks_source.users.create(
                new_user_name, new_user_password, email=new_user_email)
            users_moved_to_target = self.migration_task.execute()
            target_users = self.migration_task.ks_target.users.list()
            self.assertIn(users_moved_to_target[0], target_users)
        except Exception, e:
            self.fail(e)
        finally:
            self.migration_task.ks_source.users.delete(new_user)
            if users_moved_to_target is not None:
                self.migration_task.ks_target.users.delete(
                    users_moved_to_target[0])
