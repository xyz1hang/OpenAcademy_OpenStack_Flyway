__author__ = 'chengxue'

from tests.flow.test_base import TestBase
from flyway.common import config
from utils.db_handlers import tenants as db_handler
import utils.helper
from flow.update_projects_quotas_task import UpdateProjectsQuotasTask
from flow.tenanttask import TenantMigrationTask
from keystoneclient import exceptions as keystone_exceptions


class UpdateProjectsQuotasTest(TestBase):

    def __init__(self, *args, **kwargs):
        super(UpdateProjectsQuotasTest, self).__init__(*args, **kwargs)
        config.parse(['--config-file', '../../etc/flyway.conf'])
        self.task = UpdateProjectsQuotasTask('update_projects_quotas')
        self.migration_task = TenantMigrationTask('tenant_migration_task')
        self.s_cloud_name = utils.helper.cfg.CONF.SOURCE.os_cloud_name
        self.t_cloud_name = utils.helper.cfg.CONF.TARGET.os_cloud_name

        self.nv_source = utils.helper.get_nova_source()
        self.nv_target = utils.helper.get_nova_target()

    def test_execute(self):
        tenant_name = "tenant_name"
        tenant_to_migrate = self.migration_task.ks_source.tenants.create(
            tenant_name, "for projects quotas updating test", True)

        migrated_tenant = None
        try:
            self.migration_task.execute([tenant_name])
            self.task.execute()

            # get the tenant data that has been migrated from src to dst
            values = [tenant_name, self.s_cloud_name, self.t_cloud_name]
            tenant_data = db_handler.get_migrated_tenant(values)

            tenant_new_name = tenant_data['new_project_name']
            migrated_tenant = self.migration_task.ks_target.tenants.\
                find(name=tenant_new_name)

            # get source project quota
            src_quota = self.nv_source.quotas.get(tenant_to_migrate.id)
            # get dest project quota
            dest_quota = self.nv_source.quotas.get(migrated_tenant.id)

            self.assertIsNotNone(migrated_tenant)
            self.assertEqual(1, tenant_data['quota_updated'])
            self.assertEqual(src_quota.metadata_items,
                             dest_quota.metadata_items)
            self.assertEqual(src_quota.injected_file_content_bytes,
                             dest_quota.injected_file_content_bytes)
            self.assertEqual(src_quota.ram, dest_quota.ram)
            self.assertEqual(src_quota.floating_ips,
                             dest_quota.floating_ips)
            self.assertEqual(src_quota.instances, dest_quota.instances)
            self.assertEqual(src_quota.injected_files,
                             dest_quota.injected_files)
            self.assertEqual(src_quota.cores, dest_quota.cores)

        except keystone_exceptions.NotFound as e:
            print str(e)
        finally:
            self.clean_up(tenant_to_migrate, migrated_tenant)

    def clean_up(self, tenant_to_migrate, migrated_tenant=None):
        self.migration_task.ks_source.tenants.delete(tenant_to_migrate)
        # clean database
        filter_values = [tenant_to_migrate.name,
                         tenant_to_migrate.id,
                         utils.helper.cfg.CONF.SOURCE.os_cloud_name,
                         utils.helper.cfg.CONF.TARGET.os_cloud_name]
        db_handler.delete_migration_record(filter_values)

        if migrated_tenant:
            self.migration_task.ks_target.tenants.delete(migrated_tenant)