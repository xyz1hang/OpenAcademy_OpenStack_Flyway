__author__ = 'hydezhang'

from keystoneclient import exceptions as keystone_exceptions
from oslo.config import cfg

from tests.flow.test_base import TestBase
from flow.tenanttask import TenantMigrationTask
from utils.db_handlers import tenants


class TenantTaskTest(TestBase):
    """Unit test for Tenant migration"""

    def __init__(self, *args, **kwargs):
        super(TenantTaskTest, self).__init__(*args, **kwargs)
        self.migration_task = TenantMigrationTask('tenant_migration_task')

    def test_execute_migrate_tenant(self):
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

        except keystone_exceptions.NotFound:
            self.fail()
        finally:
            self.clean_up(tenant_to_migrate, migrated_tenant)

    def test_execute_migrate_all_tenants(self):
        tenant_name = "Tenant_on_source_cloud"
        tenant_to_migrate = self.migration_task.ks_source.tenants.create(
            tenant_name, "for tenant migration test", True)

        tenant_name2 = "Tenant_on_source_cloud2"
        tenant_to_migrate2 = self.migration_task.ks_source.tenants.create(
            tenant_name2, "for tenant migration test", True)

        migrated_tenant = None
        migrated_tenant2 = None
        try:
            # migrate nothing
            self.migration_task.execute([])

            # migrate all tenant resources
            self.migration_task.execute(None)

            # get the tenant data that has been migrated from src to dst
            values = [tenant_name, cfg.CONF.SOURCE.os_cloud_name,
                      cfg.CONF.TARGET.os_cloud_name]
            tenant_data = tenants.get_migrated_tenant(values)

            tenant_new_name = tenant_data['new_project_name']
            migrated_tenant = self.migration_task.ks_target.tenants.\
                find(name=tenant_new_name)

            self.assertIsNotNone(migrated_tenant)

            values = [tenant_name2, cfg.CONF.SOURCE.os_cloud_name,
                      cfg.CONF.TARGET.os_cloud_name]
            tenant_data2 = tenants.get_migrated_tenant(values)

            tenant_new_name2 = tenant_data2['new_project_name']
            migrated_tenant2 = self.migration_task.ks_target.tenants.\
                find(name=tenant_new_name2)

            self.assertIsNotNone(migrated_tenant2)

        except keystone_exceptions.NotFound:
            self.fail()
        finally:
            self.clean_up(tenant_to_migrate, migrated_tenant)
            self.clean_up(tenant_to_migrate2, migrated_tenant2)

    def test_migrate_duplicate_resource(self):
        tenant_name = "Tenant_on_source_cloud"
        tenant_source = self.migration_task.ks_source.tenants.create(
            tenant_name, "for tenant migration test", True)

        tenant_target = self.migration_task.ks_target.tenants.create(
            tenant_name, "for tenant migration test", True)

        self.migration_task.execute(tenant_name)
        self.clean_up(tenant_source, tenant_target)

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