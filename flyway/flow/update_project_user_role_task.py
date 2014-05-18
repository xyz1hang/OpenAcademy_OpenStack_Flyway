from utils.db_base import read_record

__author__ = 'liangshang'

from taskflow import task
from utils.helper import *

LOG = logging.getLogger(__name__)


class ProjectUserRoleBindingTask(task.Task):
    """
   Task to update quotas for all migrated projects
   """

    def get_project_pairs(self, where_dict):
        project_names = read_record('tenants',
                                    ['project_name, new_project_name'],
                                    where_dict, True)

        try:
            project_pairs = [(self.ks_source.tenants.find(name=name[0]),
                              self.ks_target.tenants.find(name=name[1]))
                             for name in project_names]
        except Exception, e:
            return None
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

        for source_user in self.ks_source.tenants. \
                list_users(source_project):
            try:
                # Check whether the user already exists
                target_user = self.ks_target.users. \
                    find(name=source_user.name)
            except Exception:
                continue
            else:
                for source_roles in self.ks_source.roles.roles_for_user(
                        user=source_user, tenant=source_project):
                    try:
                        # Check whether the role already exists
                        target_role = self.ks_target.roles. \
                            find(name=source_roles.name)
                        # Add the binding already exists
                        self.ks_target.roles. \
                            add_user_role(user=target_user,
                                          role=target_role,
                                          tenant=target_project)
                    except Exception:
                        continue

    def execute(self):
        LOG.info('bind projects, users and roles ...')
        migrated_project_pairs = \
            self.get_project_pairs({"src_cloud": self.s_cloud_name,
                                    "dst_cloud": self.t_cloud_name,
                                    "state": "proxy_created"})
        if migrated_project_pairs is not None:
            for project_pair in migrated_project_pairs:
                self.bind_roles_users(project_pair)