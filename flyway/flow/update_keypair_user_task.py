__author__ = 'chengxue'

from taskflow import task
from utils.db_handlers import keypairs as db_handler
import logging
from utils.helper import *

LOG = logging.getLogger(__name__)


class UpdateKeypairUserTask(task.Task):
    """
    Task to update quotas for all migrated projects
    """

    def __init__(self, *args, **kwargs):
        super(UpdateKeypairUserTask, self).__init__(*args, **kwargs)
        self.s_cloud_name = cfg.CONF.SOURCE.os_cloud_name
        self.t_cloud_name = cfg.CONF.TARGET.os_cloud_name
        self.t_host = \
            cfg.CONF.TARGET.os_auth_url.split("http://")[1].split(":")[0]

    def update_user_id(self, fingerprint=None, keypair_data=None):
        # get the corresponding user_id (in targer) of the
        # keypair using the user_name, which should be the
        # same as the source
        user_id = db_handler.\
            get_info_from_openstack_db(host=self.t_host,
                                       db_name='keystone',
                                       table_name='user',
                                       columns=['id'],
                                       filters={"name":
                                                keypair_data['user_name']})

        if user_id is not None:
            # because the default user to create the keypair is 'admin',
            # need to update the user_id (in target) of the keypair
            db_handler.\
                update_info_on_openstack_db(host=self.t_host,
                                            db_name='nova',
                                            table_name='key_pairs',
                                            sets={"user_id": user_id[0][0]},
                                            filters={"fingerprint":
                                                     fingerprint,
                                                     "deleted": '0'})

            keypair_data.update({'user_id_updated': "1"})
            db_handler.update_keypairs(**keypair_data)

        else:
            print "The corresponding user {0} of the key pair {1} has not " \
                  "been migrated.".format(keypair_data['user_name'],
                                          keypair_data['new_name'])

    def execute(self):
        print "keypair-user updating ..."
        # get all alive keypairs (on target) from the table
        # 'key_pairs' in 'nova'
        fingerprints = db_handler.\
            get_info_from_openstack_db(table_name="key_pairs",
                                       db_name='nova',
                                       host=self.t_host,
                                       columns=['fingerprint'],
                                       filters={"deleted": '0'})

        for one_fingerprint in fingerprints:
            values = [one_fingerprint[0], self.s_cloud_name,
                      self.t_cloud_name]
            keypair_data = db_handler.get_keypairs(values)

            if keypair_data is not None:
                if keypair_data['user_id_updated'] == "1":
                    print "The user_id of keypair {0} has been updated.".\
                        format(keypair_data['new_name'])

                elif keypair_data['state'] == "completed":
                    print "Updating user_id of keypair {0}".\
                        format(keypair_data['new_name'])
                    self.update_user_id(one_fingerprint[0], keypair_data)

                else:
                    print "Keypair {0} has not been migrated successfully".\
                        format(keypair_data['name'])