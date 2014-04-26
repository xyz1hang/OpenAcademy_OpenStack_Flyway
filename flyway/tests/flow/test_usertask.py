import mox

from flow.usertask import UserMigrationTask
from common import config
from tests.flow.test_base import TestBase
from utils.db_handlers.users import *


class UserTaskTest(TestBase):
    """Unit test for user migration"""

    def __init__(self, *args, **kwargs):
        super(UserTaskTest, self).__init__(*args, **kwargs)
        config.parse(['--config-file', '../../etc/flyway.conf'])
        self.migration_task = UserMigrationTask()
        self.mox_factory = mox.Mox()

    def test_execute_with_all_users(self):
        new_user_name = "user_that_should_not_exist2"
        new_user_password = "password"
        new_user_email = "liang.shang13@imperial.ac.uk"

        new_user_name2 = "user_that_should_not_exist3"
        new_user_password2 = "password"
        new_user_email2 = "liang.shang13@imperial.ac.uk"

        new_user, new_user2 = None, None

        try:
            new_user = self.migration_task.ks_source.users.create(
                new_user_name, new_user_password, email=new_user_email)
            new_user2 = self.migration_task.ks_source.users.create(
                new_user_name2, new_user_password2, email=new_user_email2)
            self.migration_task.execute(None)
            target_user_names = [user.name for user in
                                 self.migration_task.ks_target.users.list()]
            self.assertIn(new_user_name, target_user_names)
            self.assertIn(new_user_name2, target_user_names)
        except Exception, e:
            self.fail(e)
        finally:
            if new_user is not None:
                self.migration_task.ks_source.users.delete(new_user)
            if new_user2 is not None:
                self.migration_task.ks_source.users.delete(new_user2)
            for user in self.migration_task.ks_target.users.list():
                if user.name in [new_user_name, new_user_name2]:
                    self.migration_task.ks_target.users.delete(user)

    def test_execute_with_specified_users(self):
        new_user_name = "user_that_should_not_exist2"
        new_user_password = "password"
        new_user_email = "liang.shang13@imperial.ac.uk"

        new_user_name2 = "user_that_should_not_exist3"
        new_user_password2 = "password"
        new_user_email2 = "liang.shang13@imperial.ac.uk"

        new_user, new_user2 = None, None

        try:
            new_user = self.migration_task.ks_source.users.create(
                new_user_name, new_user_password, email=new_user_email)
            new_user2 = self.migration_task.ks_source.users.create(
                new_user_name2, new_user_password2, email=new_user_email2)
            self.migration_task.execute([new_user_name])
            target_user_names = [user.name for user in
                                 self.migration_task.ks_target.users.list()]
            self.assertIn(new_user_name, target_user_names)
            self.assertNotIn(new_user_name2, target_user_names)
        except Exception, e:
            self.fail(e)
        finally:
            delete_migrated_users()
            if new_user is not None:
                self.migration_task.ks_source.users.delete(new_user)
            if new_user2 is not None:
                self.migration_task.ks_source.users.delete(new_user2)
            for user in self.migration_task.ks_target.users.list():
                if user.name in [new_user_name, new_user_name2]:
                    self.migration_task.ks_target.users.delete(user)