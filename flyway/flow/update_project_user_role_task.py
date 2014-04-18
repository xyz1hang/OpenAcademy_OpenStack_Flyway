from utils.db_base import read_record

__author__ = 'chengxue'

from taskflow import task
from utils.db_handlers import tenants as db_handler
import logging
from utils.helper import *
from keystoneclient import exceptions as keystone_exceptions
from utils.resourcetype import ResourceType
from utils import exceptions

LOG = logging.getLogger(__name__)


class ProjectUserRoleBindingTask(task.Task):
    """
    Task to update quotas for all migrated projects
    """

    def get_project_pairs(self, where_dict):
        project_names = read_record('tenants',
                                    ['project_name, new_project_name'],
                                    where_dict, True)

        project_pairs = [(self.ks_source.tenants.find(name=name[0]),
                         self.ks_target.tenants.find(name=name[1]))
                         for name in project_names]

        return project_pairs

    def __init__(self, *args, **kwargs):
        super(ProjectUserRoleBindingTask, self).__init__(*args, **kwargs)

        self.s_cloud_name = cfg.CONF.SOURCE.os_cloud_name
        self.t_cloud_name = cfg.CONF.TARGET.os_cloud_name

        self.ks_source = get_keystone_source()
        self.ks_target = get_keystone_target()

        self.nv_source = get_nova_source()

    def bind_roles_users(self, project_pair):
        source_project = project_pair[0]
        target_project = project_pair[1]
        for source_user in self.ks_source.tenants.list_users(source_project):
            target_user = self.ks_target.users.find(name=source_user.name)
            for source_roles in self.ks_source.roles.roles_for_user(
                    user=source_user, tenant=source_project):
                target_role = self.ks_target.roles.find(name=source_roles.name)
                self.ks_target.roles.add_user_role(user=target_user,
                                                   role=target_role,
                                                   tenant=target_project)

    def execute(self):
        LOG.info('bind projects, users and roles ...')
        migrated_project_pairs = \
            self.get_project_pairs({"src_cloud": self.s_cloud_name,
                                    "dst_cloud": self.t_cloud_name,
                                    "state": "proxy_created"})
        for project_pair in migrated_project_pairs:
            self.bind_roles_users(project_pair)
