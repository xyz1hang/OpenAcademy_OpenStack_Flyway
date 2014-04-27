import logging
from taskflow import task
from utils.helper import *
from utils.db_handlers import keypairs as db_handler
from utils.db_base import *
from novaclient import exceptions as nova_exceptions


LOG = logging.getLogger(__name__)


class KeypairMigrationTask(task.Task):
    """
    Task to migrate all keypairs from the source cloud to the target cloud.
    """

    def __init__(self, *args, **kwargs):
        super(KeypairMigrationTask, self).__init__(*args, **kwargs)
        # config must be ready at this point
        self.nv_target = get_nova_target()

        self.s_cloud_name = cfg.CONF.SOURCE.os_cloud_name
        self.t_cloud_name = cfg.CONF.TARGET.os_cloud_name
        self.s_host = cfg.CONF.SOURCE. \
            os_auth_url.split("http://")[1].split(":")[0]

        self.nv_source = get_nova_source()

    def migrate_one_keypair(self, keypair_fingerprint):
        values = [keypair_fingerprint, self.s_cloud_name, self.t_cloud_name]
        keypair_data = db_handler.get_keypairs(values)

        # check for resource duplication
        try:
            duplicated = self.nv_target.keypairs.\
                find(public_key=keypair_data["public_key"])
            if duplicated:
                print "Key pair {0} has been existed in cloud {1}, stop " \
                      "migrating.".format(keypair_data["name"],
                                          keypair_data["dst_cloud"])
                # delete the corresponding assertion in the flyway database
                db_handler.delete_keypairs(values)
                return

        except nova_exceptions.NotFound:
            # irrelevant exception - swallow
            pass

        # check for resource name duplication
        new_name = keypair_data["name"]
        try:
            found = True
            while found:
                found = self.nv_target.keypairs.find(name=new_name)
                if found:
                    user_input = \
                        raw_input("duplicated tenant {0} found on cloud {1}\n"
                                  "Please type in a new name or 'abort':"
                                  .format(found.name, self.t_cloud_name))
                    if user_input == "abort":
                        # TODO: implement cleaning up and proper exit
                        return None
                    elif user_input:
                        new_name = user_input

        except nova_exceptions.NotFound:
            # irrelevant exception - swallow
            pass

        try:
            self.nv_target.keypairs.\
                create(new_name, public_key=keypair_data["public_key"])

        except IOError as (err_no, strerror):
            print "I/O error({0}): {1}".format(err_no, strerror)

        except:
            # TODO: not sure what exactly the exception will be thrown
            # TODO: upon creation failure
            print "tenant {} migration failure".format(keypair_data['name'])
            # update database record
            keypair_data = keypair_data.update({'state': "error"})
            db_handler.update_keypairs(**keypair_data)
            return

        keypair_data.update({'state': 'completed'})
        keypair_data.update({'new_name': new_name})
        db_handler.update_keypairs(**keypair_data)

    def execute(self, keypairs_to_move):
        # no resources need to be migrated
        if type(keypairs_to_move) is list and len(keypairs_to_move) == 0:
            return

        # in case only one string gets passed in
        if type(keypairs_to_move) is str:
            keypairs_to_move = [keypairs_to_move]

        # create new table if not exists
        db_handler.initialise_keypairs_mapping()

        if not keypairs_to_move:
            LOG.info("Migrating all keypairs ...")
            keypairs_to_move = []

            # get all keypairs from the table 'key_pairs' in 'nova'
            fingerprints = db_handler.\
                get_info_from_openstack_db(table_name="key_pairs",
                                           db_name='nova',
                                           host=self.s_host,
                                           columns=['fingerprint'],
                                           filters={"deleted": '0'})
            for one_fingerprint in fingerprints:
                keypairs_to_move.append(one_fingerprint[0])

        else:
            LOG.info("Migrating given keypairs of size {} ...\n"
                     .format(len(keypairs_to_move)))

        for keypair_fingerprint in keypairs_to_move:
            values = [keypair_fingerprint, self.s_cloud_name,
                      self.t_cloud_name]
            m_keypair = db_handler.get_keypairs(values)

            # add keypairs that have not been stored in the database
            if m_keypair is None:
                # get keypair information from nova using fingerprint
                result = db_handler.\
                    get_info_from_openstack_db(table_name="key_pairs",
                                               db_name='nova',
                                               host=self.s_host,
                                               columns=['*'],
                                               filters={"fingerprint":
                                                        keypair_fingerprint})

                # get the corresponding user_name (in source)
                # of the keypair using user_id
                user_name = db_handler.\
                    get_info_from_openstack_db(table_name="user",
                                               db_name='keystone',
                                               host=self.s_host,
                                               columns=['name'],
                                               filters={"id": result[0][5]})

                keypair_data = {'name': result[0][4],
                                'public_key': result[0][7],
                                'fingerprint': result[0][6],
                                'user_name': user_name[0][0],
                                'src_cloud': self.s_cloud_name,
                                'dst_cloud': self.t_cloud_name,
                                'state': "unknown",
                                'user_id_updated': "0",
                                'new_name': result[0][4]}
                db_handler.record_keypairs([keypair_data])

                LOG.info("Migrating keypair '{}'\n".format(result[0][4]))
                self.migrate_one_keypair(keypair_fingerprint)

            else:
                if m_keypair['state'] == "completed":
                    print("keypair {0} in cloud {1} has already been migrated"
                          .format(m_keypair['name'], self.s_cloud_name))

                else:
                    LOG.info("Migrating keypair '{}'\n".
                             format(m_keypair['name']))
                    self.migrate_one_keypair(keypair_fingerprint)