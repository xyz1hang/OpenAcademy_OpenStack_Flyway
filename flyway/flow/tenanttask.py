import logging

from taskflow import task
from keystoneclient import exceptions as keystone_exceptions

from utils.db_handlers import tenants
from utils import exceptions
from utils.helper import *
from utils.resourcetype import ResourceType

LOG = logging.getLogger(__name__)


class TenantMigrationTask(task.Task):
    """
    Task to migrate all tenant (project) info from the source cloud to the
    target cloud.
    """

    def __init__(self, name, **kwargs):
        super(TenantMigrationTask, self).__init__(name, **kwargs)
        # config must be ready at this point
        self.ks_source = get_keystone_source()
        self.ks_target = get_keystone_target()

    def migrate_one_tenant(self, tenant_name):
        try:
            s_tenant = self.ks_source.tenants.find(name=tenant_name)
        except keystone_exceptions.NotFound:
            # encapsulate exceptions to make it more understandable
            # to user. Other exception handling mechanism can be added later
            raise exceptions.ResourceNotFoundException(
                ResourceType.tenant, tenant_name,
                cfg.CONF.SOURCE.os_cloud_name)

        s_cloud_name = cfg.CONF.SOURCE.os_cloud_name
        t_cloud_name = cfg.CONF.TARGET.os_cloud_name

        # check whether the tenant has been migrated
        values = [tenant_name, s_cloud_name]
        m_tenant = tenants.get_migrated_tenant(values)

        if m_tenant is not None and m_tenant['state'] is "completed":
            print("tenant {0} in cloud {1} has already been migrated"
                  .format(m_tenant["project_name"], s_cloud_name))
            return

        # check for tenant name duplication
        new_tenant_name = s_tenant.name
        try:
            found = self.ks_target.tenants.find(name=s_tenant.name)
            if found:
                user_input = \
                    raw_input("duplicated tenant {0} found on cloud {1}\n"
                              "Please type in a new name or 'abort':"
                              .format(found.name, t_cloud_name))
                if user_input is "abort":
                    # TODO: implement cleaning up and proper exit
                    return None
                elif user_input:
                    new_tenant_name = user_input
        except keystone_exceptions.NotFound:
            # irrelevant exception - swallow
            pass

        # preparing for database record update
        tenant_data = {'project_name': s_tenant.name,
                       'src_uuid': s_tenant.id,
                       'src_cloud': s_cloud_name,
                       'new_project_name': new_tenant_name,
                       'dst_uuid': s_tenant.id,
                       'dst_cloud': t_cloud_name,
                       'image_migrated': '1',
                       'state': "unknown"}

        # create a new tenant
        migrated_tenant = None
        try:
            migrated_tenant = self.ks_target.tenants.create(
                new_tenant_name,
                s_tenant.description,
                s_tenant.enabled)
        except IOError as (err_no, strerror):
            print "I/O error({0}): {1}".format(err_no, strerror)
        except:
            # TODO: not sure what exactly the exception will be thrown
            # TODO: upon creation failure
            print "tenant {} migration failure".format(s_tenant.name)
            # update database record
            tenant_data.update({'state': "error"})
            tenants.record_tenant_migrated(**tenant_data)
            return

        # add the "admin" as the default user - admin - of
        # the tenant migrated.
        # Actual users involved in the tenant can be
        # added in and replace default one later
        admin = self.ks_target.users.find(name="admin")
        role = self.ks_target.roles.find(name="admin")
        migrated_tenant.add_user(admin, role)

        # record in database
        tenant_data.update({'dst_uuid': migrated_tenant.id})
        tenant_data.update({'state': 'proxy_created'})

        tenants.record_tenant_migrated([tenant_data])

    def execute(self, tenants_to_move=None):

        """execute the tenant migration task

        :param tenants_to_move: the tenant to move. If the not specified
        or length equals to 0 all tenant will be migrated, otherwise only
        specified tenant will be migrated
        """

        # convert tenants_to_move to list in case only
        # one string gets passed in
        if type(tenants_to_move) is str:
            tenants_to_move = [tenants_to_move]

        # create new table if not exists or
        # delete all data in order to be able to recording new migration
        tenants.initialise_tenants_mapping()

        if not tenants_to_move or len(tenants_to_move) == 0:
            LOG.info("Migrating all tenants ...")
            tenants_to_move = []
            for tenant in self.ks_source.tenants.list():
                tenants_to_move.append(tenant.name)
        else:
            LOG.info("Migrating given tenants of size {} ...\n"
                     .format(len(tenants_to_move)))

        for source_tenant in tenants_to_move:
            LOG.info("Migrating tenant '{}'\n".format(source_tenant))
            self.migrate_one_tenant(source_tenant)