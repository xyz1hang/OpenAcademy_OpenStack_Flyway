__author__ = 'chengxue'

from taskflow import task
from utils.db_handlers import tenants as db_handler
import logging
from utils.helper import *
from keystoneclient import exceptions as keystone_exceptions
from utils.resourcetype import ResourceType
from utils import exceptions

LOG = logging.getLogger(__name__)


class UpdateProjectsQuotasTask(task.Task):
    """
    Task to update quotas for all migrated projects
    """

    def __init__(self, *args, **kwargs):
        super(UpdateProjectsQuotasTask, self).__init__(*args, **kwargs)

        self.s_cloud_name = cfg.CONF.SOURCE.os_cloud_name
        self.t_cloud_name = cfg.CONF.TARGET.os_cloud_name

        self.ks_source = get_keystone_source()
        self.nv_source = get_nova_source()
        self.nv_target = get_nova_target()

    def update_quota(self, tenant_name=None, quota=None):
        if not quota:
            LOG.info('Nothing to be updated.')
            return

        if not tenant_name:
            raise Exception("Tenant name cannot be null.")

        ks = get_keystone_target()
        try:
            tenant = ks.tenants.find(name=tenant_name)

        except keystone_exceptions.NotFound:
            # encapsulate exceptions to make it more understandable
            # to user. Other exception handling mechanism can be added later
            raise exceptions.ResourceNotFoundException(
                ResourceType.tenant, tenant_name, self.t_cloud_name)

        if tenant is not None:
            self.nv_target.quotas.update(tenant.id,
                                         metadata_items=quota.metadata_items,
                                         injected_file_content_bytes=
                                         quota.injected_file_content_bytes,
                                         injected_file_path_bytes=None,
                                         ram=quota.ram,
                                         floating_ips=quota.floating_ips,
                                         instances=quota.instances,
                                         injected_files=quota.injected_files,
                                         cores=quota.cores,
                                         key_pairs=None,
                                         security_groups=None,
                                         security_group_rules=None)

    def execute(self):
        print "project quota updating ..."
        tenants = self.ks_source.tenants.list()

        for tenant in tenants:
            tenant_name = tenant.name
            # get the tenant data that has been migrated from src to dst
            values = [tenant_name, self.s_cloud_name, self.t_cloud_name]
            tenant_data = db_handler.get_migrated_tenant(values)

            # only update quotas for project that has been completed migrated
            if tenant_data is not None:
                if tenant_data['state'] == "proxy_created":
                    if tenant_data['quota_updated'] == '1':
                        print "The quota of project {0} has been updated.".\
                            format(tenant_data['project_name'])

                    else:
                        new_name_dst = tenant_data['new_project_name']

                        # get source project quota
                        src_quota = self.nv_source.quotas.get(tenant.id)
                        # update destination project quota
                        self.update_quota(new_name_dst, src_quota)

                        tenant_data.update({'quota_updated': '1'})
                        db_handler.update_migration_record(**tenant_data)

                else:
                    print "The corresponding project {0} " \
                          "has not been migrated.".\
                        format(tenant_data['project_name'])