__author__ = 'hydezhang'

from keystoneclient import exceptions as keystone_exceptions
from oslo.config import cfg

from tests.flow.test_base import TestBase
from flow.tenanttask import TenantMigrationTask
from common import config
from utils.db_handlers import tenants


class TenantTaskTest(TestBase):
    """Unit test for Tenant migration"""

    def __init__(self, *args, **kwargs):
        super(TenantTaskTest, self).__init__(*args, **kwargs)
        config.parse(['--config-file', '../../etc/flyway.conf'])
        self.migration_task = TenantMigrationTask('tenant_migration_task')

    def test_execute(self):
        tenant_name = "Tenant_on_source_cloud"
        tenant_to_migrate = self.migration_task.ks_source.tenants.create(
            tenant_name, "for tenant migration test", True)

        migrated_tenant = None
        try:
            self.migration_task.execute(tenant_name)

            # get the tenant data that has been migrated from src to dst
            values = [tenant_name, cfg.CONF.SOURCE.os_cloud_name,
                      cfg.CONF.TARGET.os_cloud_name]
            tenant_data = tenants.get_migrated_tenant(values)

            tenant_new_name = tenant_data['new_project_name']
            migrated_tenant = self.migration_task.ks_target.tenants.\
                find(name=tenant_new_name)

            self.assertIsNotNone(migrated_tenant)

        except keystone_exceptions.NotFound as e:
            print str(e)
        finally:
            self.clean_up(tenant_to_migrate, migrated_tenant)

    def clean_up(self, tenant_to_migrate, migrated_tenant=None):
        self.migration_task.ks_source.tenants.delete(tenant_to_migrate)
        # clean database
        filter_values = [tenant_to_migrate.name,
                         tenant_to_migrate.id,
                         cfg.CONF.SOURCE.os_cloud_name,
                         cfg.CONF.TARGET.os_cloud_name]
        tenants.delete_migration_record(filter_values)

        if migrated_tenant:
            self.migration_task.ks_target.tenants.delete(migrated_tenant)