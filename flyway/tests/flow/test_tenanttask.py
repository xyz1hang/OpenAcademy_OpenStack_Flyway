from flyway.utils.helper import get_clients

__author__ = 'hydezhang'

import sys

from testtools import TestCase
import mox

sys.path.append('../..')
from flyway.flow.tenanttask import TenantMigrationTask
from flyway.common import config

from keystoneclient import exceptions as keystone_exceptions


class TenantTaskTest(TestCase):
    """Unit test for Tenant migration"""

    def __init__(self, *args, **kwargs):
        super(TenantTaskTest, self).__init__(*args, **kwargs)
        config.parse(['--config-file', '../../etc/flyway.conf'])
        self.migration_task = TenantMigrationTask('tenant_migration_task',
                                                  "Tenant_on_source_cloud")
        clients = get_clients()
        self.migration_task.ks_source = clients.get_source()
        self.migration_task.ks_target = clients.get_destination()
        self.mox_factory = mox.Mox()

    def test_execute(self):
        tenant_name = "Tenant_on_source_cloud"
        tenant_to_migrate = self.migration_task.ks_source.tenants.create(
            tenant_name, "for tenant migration test", True)

        self.migration_task.execute()

        try:
            migrated_tenant = self.migration_task.ks_target.tenants.find(
                name=tenant_name)

            self.assertEqual(tenant_to_migrate, migrated_tenant.name)

            self.migration_task.ks_source.tenants.delete(tenant_to_migrate)
            self.migration_task.ks_target.tenants.delete(migrated_tenant)

        except keystone_exceptions.NotFound:
            self.migration_task.ks_source.tenants.delete(tenant_to_migrate)
