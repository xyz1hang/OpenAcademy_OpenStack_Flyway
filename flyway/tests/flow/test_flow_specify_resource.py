__author__ = 'chengxue'

from tests.flow.test_base import TestBase
from flyway.common import config
from flyway.flow import flow
from flyway.utils.helper import *
from keystoneclient import exceptions as ks_exceptions
from utils.db_handlers import tenants
from utils.db_handlers import users


class UpdateProjectsQuotasTest(TestBase):

    def __init__(self, *args, **kwargs):
        super(UpdateProjectsQuotasTest, self).__init__(*args, **kwargs)

        self.ks_source = get_keystone_source()
        self.ks_target = get_keystone_target()
        self.s_cloud_name = cfg.CONF.SOURCE.os_cloud_name
        self.t_cloud_name = cfg.CONF.TARGET.os_cloud_name

    def test_execute(self):
        tenant_name = "tenant_test"
        tenant_to_migrate = self.ks_source.tenants.create(
            tenant_name, "for testing", True)

        user_name = "tester"
        user_to_migrate = self.ks_source.users.create(
            user_name, password="password",
            email="cheng.xue13@imperial.ac.uk",
            tenant_id=tenant_to_migrate.id)

        values = {'tenants_to_move': [tenant_name],
                  'flavors_to_migrate': [],
                  'images_to_migrate': [],
                  'tenant_to_process': [],
                  'keypairs_to_move': [],
                  'name_of_roles_to_move': [],
                  'users_to_move': [user_name]}

        flow.execute(values)

        tenant_target = None
        user_target = None
        values_t = [tenant_name, self.s_cloud_name, self.t_cloud_name]
        values_u = [user_name, self.s_cloud_name, self.t_cloud_name]
        try:
            tenant_target = self.ks_target.tenants.find(name=tenant_name)
            user_target = self.ks_target.users.find(name=user_name)

            self.assertIsNotNone(tenant_target)
            self.assertIsNotNone(user_target)

            all_users = self.ks_target.users.list(tenant_id=tenant_target.id)
            self.assertIn(user_target, all_users)

            tenant_data = tenants.get_migrated_tenant(values_t)
            user_data = users.get_migrated_user(values_u)

            self.assertEqual("proxy_created", tenant_data['state'])
            self.assertEqual("completed", user_data['state'])

        except ks_exceptions.NotFound:
            self.ks_source.tenants.delete(tenant_to_migrate)
            self.ks_source.users.delete(user_to_migrate)
            return

        finally:
            self.ks_source.tenants.delete(tenant_to_migrate)
            self.ks_source.users.delete(user_to_migrate)
            if tenant_target is not None:
                self.ks_target.tenants.delete(tenant_target)
            if user_target is not None:
                self.ks_target.users.delete(user_target)
            values_t = [tenant_name, tenant_to_migrate.id,
                        self.s_cloud_name, self.t_cloud_name]
            tenants.delete_migration_record(values_t)
            users.delete_migrated_users()