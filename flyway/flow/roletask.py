__author__ = 'tianchen'

from utils.helper import *
from utils.db_handlers.roles import *
from taskflow import task
import taskflow.engines
from taskflow.patterns import unordered_flow as uf

LOG = logging.getLogger(__name__)


def delete_role(role, target):
    """
    delete a role from the target cloud
    :param role: a role object
    :param target: keystone client of the target cloud
    """
    for r in target.roles.list():
        LOG.debug('try to delete role'+str(role.name))
        if r.name == role.name:
            target.roles.delete(r)
            LOG.info('role deleted: '+str(role.name))


class MigrateOneRole(task.Task):
    """
    Task to create a role in the target cloud.
    """
    def execute(self, role, target):
        """
        :param role: a role object
        :param target: keystone client of the target cloud
        """
        try:
            LOG.debug('try to migrate role'+str(role.name))
            target.roles.create(role.name)
            update_complete(role.name)

            LOG.info('role migrated: '+str(role.name))
            return True
        except :
            update_error(role.name)
            return False

    def revert(self, role, target):
        """
        :param role: a role object
        :param target: keystone client of the target cloud
        """
        try:
            delete_role(role, target)
            update_cancel(role.name)
            LOG.info('revert migrating: '+str(role.name))

        except:
            print 'failure'


class RoleMigrationTask(task.Task):
    """
    Task to migrate all roles and user-tenant role mapping from the source
    cloud to the target cloud.
    """

    def __init__(self, *args, **kwargs):
        super(RoleMigrationTask, self).__init__(*args, **kwargs)
        # get keystone clients for source and target clouds
        self.ks_source = get_keystone_source()
        self.ks_target = get_keystone_target()

    @staticmethod
    def list_roles(keystone_client):
        """
        list all role objects one the cloud using its keystone_client
        :param keystone_client:
        """
        return keystone_client.roles.list()

    @staticmethod
    def list_names(roles):
        """
        return a list of names of with respect to roles
        :param roles: a list of role objects
        """
        return [role.name for role in roles]

    def get_roles_to_move(self):
        """
        return a list of role objects should be migrated to the target cloud
        """
        roles_in_source = self.list_roles(self.ks_source)
        target_role_names = self.list_names(self.ks_target.roles.list())
        return [role for role in roles_in_source
                if role.name not in target_role_names]

    def execute(self, roles_to_migrate):
        """
        migrate specified roles to the target cloud
        :param roles_to_migrate: roles to be migrated to the target cloud.
        if None, then all roles exist on source but not on target will be migrated
        """
        if type(roles_to_migrate) is list and \
           len(roles_to_migrate) == 0:
            return

        LOG.info('Start migrating specified roles from source to target..')

        roles_to_move = self.get_roles_to_move()
        initialise_roles_mapping(self.list_names(roles_to_move))

        flow = uf.Flow('migrate_roles')
        store = {'target': self.ks_target}

        if roles_to_migrate is None:
            for role in roles_to_move:
                store[role.name] = role
                flow.add(MigrateOneRole(role.name, rebind=[role.name]))

        else:
            for role in roles_to_move:
                if role.name in roles_to_migrate:
                    store[role.name] = role
                    flow.add(MigrateOneRole(role.name, rebind=[role.name]))

        engine = taskflow.engines.load(flow, store)
        engine.run()

        LOG.info('Migration Complete.')

    def revert(self, roles_to_migrate, *args, **kwargs):
        """
        revert process correspond to execute
        """
        if type(roles_to_migrate) is list and \
           len(roles_to_migrate) == 0:
            return

        LOG.info('Start reverting process...')

        roles_to_move = self.get_roles_to_move()

        if roles_to_migrate is None:
            for role in roles_to_move:
                delete_role(role, self.ks_target)
                update_cancel(role.name)
        else:
            for role in roles_to_move:
                if role.name in roles_to_migrate:
                    delete_role(role, self.ks_target)
                    update_cancel(role.name)

        LOG.info('Reverting Complete.')
