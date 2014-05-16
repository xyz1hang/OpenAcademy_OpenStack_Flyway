from taskflow import task

from utils.db_handlers.users import set_user_complete, \
    initialise_users_mapping, delete_all_users_mapping
from utils.helper import *

LOG = logging.getLogger(__name__)


class UserMigrationTask(task.Task):
    """
    Task to migrate all user info from the source cloud to the target cloud.
    """

    def __init__(self, *args, **kwargs):
        super(UserMigrationTask, self).__init__(*args, **kwargs)
        self.ks_source = get_keystone_source()
        self.ks_target = get_keystone_target()
        self.migrated_users_in_source = None

        self.target_user_names = [user.name for user in
                                  self.ks_target.users.list()]

    def migrate_one_user(self, user):
        LOG.info("Begin to migrate user {0}".format(user.name))
        migrated_user = None
        if user.name not in self.target_user_names:
            password = generate_new_password(user.email)

            try:
                migrated_user = self.ks_target.users.create(user.name,
                                                            password,
                                                            user.email,
                                                            enabled=True)
            except Exception, e:
                LOG.error("There is an error while migrating user {0}"
                          .format(user))
                LOG.error("The error is {0}".format(e.message))
            else:
                LOG.info("Succeed to migrate user {0}".format(user.name))
                set_user_complete(user)
        return migrated_user

    def get_source_users(self, users_to_move):
        """
        Get users which are to be moved from self.ks_source.
        If param users_to_move is None, return all users in source
        """
        return [user for user in self.ks_source.users.list()
                if user.name not in self.target_user_names] \
            if users_to_move is None \
            else [user for user in self.ks_source.users.list()
                  if user.name in users_to_move
                  and user.name not in self.target_user_names]

    def execute(self, users_to_move):

        if type(users_to_move) is list and len(users_to_move) == 0:
            return

        self.migrated_users_in_source = self.get_source_users(users_to_move)

        initialise_users_mapping(self.migrated_users_in_source, self.target_user_names)

        migrated_users = []
        for user in self.migrated_users_in_source:
            migrated_user = self.migrate_one_user(user)
            if migrated_user is not None:
                migrated_users.append(migrated_user)

    def revert_users(self):
        migrated_user_names = [user.name for user in
                               self.migrated_users_in_source]
        for user in self.ks_target.users.list():
            if user.name in migrated_user_names:
                self.ks_target.users.delete(user)

    def revert(self, *args, **kwargs):
        if self.migrated_users_in_source is not None:
            #Firstly delete the migrated data in target
            self.revert_users()
            #Then delete the records in DB
            delete_all_users_mapping(self.migrated_users_in_source)
