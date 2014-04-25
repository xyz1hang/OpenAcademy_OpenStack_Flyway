from flow.roletask import RoleMigrationTask
from flow.usertask import UserMigrationTask
from tests.flow.test_base import TestBase
from flyway.common import config
from utils.db_handlers import tenants as db_handler
import utils.helper
from flow.update_project_user_role_task import ProjectUserRoleBindingTask
from flow.tenanttask import TenantMigrationTask
from keystoneclient import exceptions as keystone_exceptions


class UpdateProjectUserRoleTest(TestBase):
    def __init__(self, *args, **kwargs):
        super(UpdateProjectUserRoleTest, self).__init__(*args, **kwargs)
        config.parse(['--config-file', '../../etc/flyway.conf'])
        self.binding_task = ProjectUserRoleBindingTask(
            'update_projects_quotas')
        self.tenant_migration_task = TenantMigrationTask(
            'tenant_migration_task')
        self.user_migration_task = UserMigrationTask(
            'user_migration_task')
        self.role_migration_task = RoleMigrationTask(
            'role_migration_task')
        self.s_cloud_name = utils.helper.cfg.CONF.SOURCE.os_cloud_name
        self.t_cloud_name = utils.helper.cfg.CONF.TARGET.os_cloud_name

        self.nv_source = utils.helper.get_nova_source()
        self.nv_target = utils.helper.get_nova_target()

    def test_execute(self):
        tenant_name = "tenant_name"
        tenant_to_migrate = self.tenant_migration_task.ks_source.tenants. \
            create(tenant_name, "for projects quotas updating test", True)
        user_name = "user_name"
        user_to_migrate = self.tenant_migration_task.ks_source.users. \
            create(name=user_name, password="password")
        role_name = "role_name"
        role_to_migrate = self.tenant_migration_task.ks_source.roles. \
            create(role_name)
        self.tenant_migration_task.ks_source.roles.add_user_role(
            user_to_migrate,
            role_to_migrate,
            tenant_to_migrate)
        self.assertIn(role_to_migrate, self.tenant_migration_task.ks_source.
                      roles.roles_for_user(user_to_migrate,
                                           tenant_to_migrate))

        migrated_tenant = None
        migrated_user = None
        migrated_role = None
        try:
            self.tenant_migration_task.execute([tenant_name])
            self.role_migration_task.execute()
            self.user_migration_task.execute(None)
            self.binding_task.execute()

            # get the tenant data that has been migrated from src to dst
            values = [tenant_name, self.s_cloud_name, self.t_cloud_name]
            tenant_data = db_handler.get_migrated_tenant(values)
            tenant_new_name = tenant_data['new_project_name']

            migrated_tenant = self.tenant_migration_task.ks_target.tenants. \
                find(name=tenant_new_name)
            migrated_user = self.user_migration_task.ks_target.users. \
                find(name=user_name)
            migrated_role = self.role_migration_task.ks_target.roles. \
                find(name=role_name)

            self.assertIn(migrated_role, self.tenant_migration_task.ks_target.
                          roles.roles_for_user(migrated_user,
                                               migrated_tenant))

        except keystone_exceptions.NotFound as e:
            print str(e.message)
            self.fail()
        finally:
            self.clean_up(tenant_to_migrate, migrated_tenant,
                          user_to_migrate, migrated_user,
                          role_to_migrate, migrated_role)

    def clean_up(self, tenant_to_migrate, migrated_tenant,
                 user_to_migrate, migrated_user,
                 role_to_migrate, migrated_role):
        self.tenant_migration_task.ks_source.tenants.delete(tenant_to_migrate)
        self.tenant_migration_task.ks_source.roles.delete(role_to_migrate)
        self.tenant_migration_task.ks_source.users.delete(user_to_migrate)

        if migrated_tenant:
            self.tenant_migration_task.ks_target.tenants. \
                delete(migrated_tenant)
        if migrated_role:
            self.tenant_migration_task.ks_target.roles. \
                delete(migrated_role)
        if migrated_user:
            self.tenant_migration_task.ks_target.users. \
                delete(migrated_user)

    """
    def test_clean_all_data(self):
        '''This function is used to delete all corresponding data
           in case of duplication'''
        for user in self.tenant_migration_task.ks_source.users.list():
            if user.name == 'user_name':
                self.tenant_migration_task.ks_source.users.delete(user)
        for role in self.tenant_migration_task.ks_source.roles.list():
            if role.name == 'role_name':
                self.tenant_migration_task.ks_source.roles.delete(role)
        for tenant in self.tenant_migration_task.ks_source.tenants.list():
            if tenant.name == 'tenant_name':
                self.tenant_migration_task.ks_source.tenants.delete(tenant)

        for user in self.tenant_migration_task.ks_target.users.list():
            if user.name == 'user_name':
                print user.name
                self.tenant_migration_task.ks_target.users.delete(user)
        for role in self.tenant_migration_task.ks_target.roles.list():
            if role.name == 'role_name':
                self.tenant_migration_task.ks_target.roles.delete(role)
        for tenant in self.tenant_migration_task.ks_target.tenants.list():
            if tenant.name == 'tenant_name':
                self.tenant_migration_task.ks_target.tenants.delete(tenant)
    """
