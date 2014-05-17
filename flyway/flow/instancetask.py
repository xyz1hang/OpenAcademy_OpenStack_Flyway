from datetime import datetime
from utils.migration_states import InstanceMigrationState

__author__ = "hydezhang"

import traceback
import time

from taskflow import task

from novaclient import exceptions as nova_exceptions
from keystoneclient import exceptions as keystone_exceptions
from glanceclient import exc as glance_exceptions

from utils import exceptions
from utils.db_handlers import instances, tenants, flavors, images, keypairs
from utils.helper import *
from utils.resourcetype import ResourceType


LOG = logging.getLogger(__name__)


class InstanceMigrationTask(task.Task):
    """
    Task to migrate all instances from the source cloud to the target cloud.
    """

    def __init__(self, name, **kwargs):
        super(InstanceMigrationTask, self).__init__(name, **kwargs)
        self.ks_source = get_keystone_source()
        self.ks_target = get_keystone_target()

        self.s_cloud_name = cfg.CONF.SOURCE.os_cloud_name
        self.t_cloud_name = cfg.CONF.TARGET.os_cloud_name
        self.valid_states = ['ACTIVE', 'PAUSED', 'SUSPENDED', 'SHUTOFF']

        # create new table if not exists
        instances.initialise_vm_mapping()

    def retrieve_flavor(self, server, s_nova_client, t_nova_client):
        """ function to safely get the corresponding flavor on destination
         cloud of the flavor which has been used by the server instance on
         source cloud

        :param server: server instance to migrate
        :param s_nova_client: nova client of the source cloud
        :param t_nova_client: nova client of the target cloud
        :return: flavor to be used by the server instance on destination
        :raise exceptions.ResourceNotFoundException:
        """

        # find original flavor used on the source cloud
        s_flavor_id = server.flavor['id']
        try:
            s_flavor = s_nova_client.flavors.find(id=s_flavor_id)
        except nova_exceptions.NotFound:
            raise exceptions.ResourceNotFoundException(
                ResourceType.vm, s_flavor_id, self.s_cloud_name)

        # check whether the flavor has been migrated or not
        filter_values = [s_flavor.name, s_flavor.id, self.s_cloud_name,
                         self.t_cloud_name]
        m_flavor = flavors.get_migrated_flavor(filter_values)

        if not m_flavor:
            LOG.info("Flavor '{0}' required by instance [ID: {1}, Name: {2}] "
                     "has been migrated yet, use default solution."
                     .format(s_flavor.name, server.id, server.name))
            try:
                m_flavor = t_nova_client.flavors.find(id=server.flavor['id'])
            except Exception:
                return None

            return m_flavor

        # try to get its corresponding flavor on destination cloud
        dst_flavor_id = m_flavor['dst_uuid']
        try:
            flavor_to_use = t_nova_client.flavors.find(id=dst_flavor_id)
        except nova_exceptions.NotFound:
            LOG.info("Migrated flavor '{0}' does not exist on destination "
                     "cloud '{1}'".format(s_flavor.name, self.t_cloud_name))
            raise exceptions.ResourceNotFoundException(
                ResourceType.vm, s_flavor_id, self.s_cloud_name)

        return flavor_to_use

    def retrieve_image(self, server):
        """ function to safely get the corresponding image on destination
         cloud of the image which has been used by the server instance on
         source cloud

        :param server: server instance to migrate
        :return: image to be used by the server instance on destination
        :raise exceptions.ResourceNotFoundException:
        """

        # find the original image used on source cloud
        gl_source = get_glance_client(self.ks_source)
        s_image_id = server.image['id']
        try:
            s_image = gl_source.images.get(s_image_id)
        except glance_exceptions.HTTPNotFound:
            raise exceptions.ResourceNotFoundException(
                ResourceType.image, s_image_id, self.s_cloud_name)

        # check whether the image has been migrated or not
        filters = {"src_image_name": s_image.name,
                   "src_uuid": s_image.id,
                   "src_cloud": self.s_cloud_name,
                   "dst_cloud": self.t_cloud_name}

        migrated_images = images.get_migrated_image(filters)
        m_image = migrated_images[0] if migrated_images else None

        # check for duplicated records
        if migrated_images and len(migrated_images) > 1:
            LOG.error("Error - Multiple migration records found for "
                      "image '{0}' in cloud '{1}'"
                      .format(filters['src_image_name'], filters['src_cloud']))
            return None

        if not m_image:
            LOG.info("Image '{0}' required by instance [ID: {1}, Name: {2}] "
                     "hasn't been migrated yet."
                     .format(s_image.name, server.id, server.name))
            return None

        # try to get its corresponding image on destination cloud
        gl_target = get_glance_client(self.ks_target)
        dst_image_id = m_image['dst_uuid']
        try:
            image_to_use = gl_target.images.get(dst_image_id)
        except glance_exceptions.HTTPNotFound:
            LOG.info("Migrated image '{0}' does not exist on destination "
                     "cloud '{1}'".format(s_image.name, self.t_cloud_name))
            raise exceptions.ResourceNotFoundException(
                ResourceType.vm, s_image_id, self.s_cloud_name)

        return image_to_use

    def retrieve_keypair(self, server, s_nova_client, t_nova_client):
        """ function to safely get the corresponding keypair on destination
         cloud of the keypair which has been used by the server instance on
         source cloud

        :param server: server instance to migrate
        :param s_nova_client: nova client of the source cloud
        :param t_nova_client: nova client of the target cloud
        :return: keypair to be used by the server instance on destination
        :raise exceptions.ResourceNotFoundException:
        """

        # find the original keypair used on source cloud
        s_keypair_name = server.key_name
        try:
            s_keypair = s_nova_client.keypairs.find(name=s_keypair_name)
        except nova_exceptions.NotFound:
            raise exceptions.ResourceNotFoundException(
                ResourceType.keypair, s_keypair_name, self.s_cloud_name)

        # check whether the keypair has been migrated or not
        filter_values = [s_keypair.fingerprint, self.s_cloud_name,
                         self.t_cloud_name]
        migrated_keypairs = keypairs.get_keypairs(filter_values)
        m_keypair = migrated_keypairs if migrated_keypairs else None
        if not m_keypair:
            LOG.info("keypair '{0}' required by instance [ID: {1}, Name: {2}] "
                     "hasn't been migrated yet."
                     .format(s_keypair.name, server.id, server.name))
            return None

        # try to get its corresponding keypair on destination cloud
        dst_keypair_name = m_keypair['name']
        try:
            keypair_to_use = t_nova_client.keypairs.find(name=dst_keypair_name)
        except nova_exceptions.NotFound:
            LOG.info(
                "Migrated keypair ['{0}'] does not"
                " exist on destination cloud '{1}'"
                .format(s_keypair.name, self.t_cloud_name))
            raise exceptions.ResourceNotFoundException(
                ResourceType.vm, s_keypair_name, self.s_cloud_name)

        return keypair_to_use

    @staticmethod
    def save_status(result, vm):
        # prepare for updating database record
        data_update = {'src_uuid': vm.src_uuid,
                       'src_cloud': vm.src_cloud,
                       'dst_cloud': vm.dst_cloud,
                       'dst_uuid': vm.id}

        LOG.info("Instance [%s] migration state: '%s'" % (vm.name, result))
        # update database record
        data_update.update({'migration_state': result})
        instances.update_migration_record(**data_update)

    @staticmethod
    def poll_vms_status(nova_client, vms_to_poll, ok_m_state, break_m_state,
                        ok_status, break_status='ERROR',
                        call_back=None, poll_interval=5, max_polls=10,
                        verbose=False):

        """function to check for states of s list of given server instance

        :param nova_client: nova python client that used to retrieve data
        about instance on the OpenStack deployment
        :param vms_to_poll: List of server instance objects to poll state for
        :param ok_m_state: the migration state to use when vms' are
                           in good status
        :param break_m_state: the migration state to use when vms' are
                              in bad status
        :param ok_status: List of user defined status regarded as OK
        :param break_status: List of user defined error status
        :param call_back: function to call upon state retrieved
        :param poll_interval: time between two consecutive polls
        :param max_polls: maximum number of poll attempt for each instance
        :param verbose: flag to indicate whether to be verbose during polling
        """

        status_ok_servers = []

        num_of_poll = [0] * len(vms_to_poll)
        while len(vms_to_poll) > 0:

            for vm in vms_to_poll:
                # check for max number of polls
                index = vms_to_poll.index(vm)
                if num_of_poll[index] == max_polls:
                    LOG.info(
                        "Maximum number of poll({0}) has been exceeded for "
                        "instance [Name: {1}, ID: {2}]".
                        format(max_polls, vm.name, vm.id))
                    call_back(result="ERROR", vm=vm)
                    vms_to_poll.remove(vm)
                    del num_of_poll[index]
                    continue

                if verbose:
                    LOG.info("polling status of instance [Name: {0}, ID: {1}].."
                             "....".format(vm.name, vm.id))
                try:
                    server = nova_client.servers.get(vm.id)
                    status = getattr(server, 'status').upper()
                except nova_exceptions.NotFound:
                    LOG.info("Server instance [Name: {0}, ID: {1}] doesn't "
                             "exist in tenant {2}"
                             .format(vm.name, vm.id, nova_client.projectid))
                    status = break_status

                result = ok_m_state if status in ok_status else break_m_state \
                    if status in break_status else None
                if result:
                    LOG.info("VM[%s] status: '%s'" % (vm.name, status))
                    # collection vms in good state
                    if status in ok_status:
                        status_ok_servers.append(vm)
                    # stop polling for this instance
                    vms_to_poll.remove(vm)
                    del num_of_poll[index]
                    if call_back:
                        try:
                            call_back(result=result, vm=vm)
                        except Exception:
                            traceback.print_exc()
                            pass
                    return

                num_of_poll[index] += 1
                time.sleep(poll_interval)

        # return all vms in good states
        return status_ok_servers

    def create_vm(self, server, s_nova_client, t_nova_client):

        # preparing flavor
        flavor_to_use = self.retrieve_flavor(server, s_nova_client,
                                             t_nova_client)
        # preparing image
        image_to_use = self.retrieve_image(server)

        # preparing keypair
        keypair_to_use = None
        if server.key_name:
            keypair_to_use = self.retrieve_keypair(server, s_nova_client,
                                                   t_nova_client)
        print 'flavor to use:', flavor_to_use
        proxy_vm = t_nova_client.servers.create(name=server.name,
                                                image=image_to_use,
                                                flavor=flavor_to_use,
                                                key_name=keypair_to_use.name)
        return proxy_vm

    def create_proxy_vm(self, server, s_nova_client, t_nova_client,
                        ignore_vm_state=False):

        """function to create proxy server instance on destination cloud for
        instance on source cloud

        :param server: server instance to migrate
        :param s_nova_client: nova client of source cloud
        :param t_nova_client: nova client of destination cloud
        :param ignore_vm_state: flag to indicate whether to ignore instance
        state during migration
        :return: proxy server instance object
        """

        # preparing for database record
        # First check whether the vm has been previously migrated
        src_tenant = s_nova_client.projectid
        dst_tenant = t_nova_client.projectid
        filters = {"src_server_name": server.name,
                   "src_uuid": server.id,
                   "src_tenant": src_tenant,
                   "src_cloud": self.s_cloud_name,
                   "dst_cloud": self.t_cloud_name}

        migrated_instances = instances.get_migrated_vm(**filters)
        m_instance = migrated_instances[0] if migrated_instances else None

        # check for duplicated record
        if migrated_instances and len(migrated_instances) > 1:
            LOG.error("Error - Multiple migration records found for "
                      "instance '{0}' from tenant '{1}' in cloud '{2}'"
                      .format(filters['src_server_name'], filters['src_tenant'],
                              filters['src_cloud']))
            return None

        if m_instance:
            # states that are valid starting point of proxy creation
            starting_states = [InstanceMigrationState.default,
                               InstanceMigrationState.launching_proxy,
                               InstanceMigrationState.error,
                               InstanceMigrationState.proxy_instance_missing,
                               InstanceMigrationState.proxy_launching_failed]
            # check whether destination id is not or not
            # i.e whether the proxy exists on destination or not
            migration_state = m_instance['migration_state']
            if migration_state not in starting_states:
                return

            # if not completed or proxy hasn't been created then
            # we picked it up from the database record
            migration_record = m_instance

        else:  # else create new record for this instance
            migration_record = {
                'src_server_name': server.name,
                'src_uuid': server.id,
                'src_cloud': self.s_cloud_name,
                'src_tenant': src_tenant,
                'dst_server_name': server.name,
                'dst_cloud': self.t_cloud_name,
                'dst_uuid': 'NULL',
                'dst_tenant': dst_tenant,
                'migration_state': InstanceMigrationState.launching_proxy}

            instances.record_vm_migrated([migration_record])

        # check instance status
        instance_state = getattr(server, 'status')
        if not ignore_vm_state and instance_state not in self.valid_states:
            LOG.info("Skipping VM[%s] due to state '%s'"
                     % (server.name, getattr(server, 'status')))

            migration_record.update({'migration_state':
                                         InstanceMigrationState.skipped})
            instances.update_migration_record(**migration_record)
            return None

        LOG.info("creating proxy instance in destination cloud for instance "
                 "'%s' with source id '%s'" % (server.name, server.id))

        try:
            p_server = self.create_vm(server, s_nova_client, t_nova_client)

            # store source vm id, source cloud name destination cloud name in
            # this target vm object in order to update database records
            setattr(p_server, 'src_uuid', migration_record['src_uuid'])
            setattr(p_server, 'src_cloud', migration_record['src_cloud'])
            setattr(p_server, 'dst_cloud', migration_record['dst_cloud'])

            # check for VM spawning status
            state_ok_servers = self.poll_vms_status(
                nova_client=t_nova_client,
                vms_to_poll=[p_server],
                ok_status=self.valid_states,
                ok_m_state=InstanceMigrationState.proxy_launched,
                break_m_state=InstanceMigrationState.proxy_launching_failed,
                call_back=self.save_status, verbose=True)

            return state_ok_servers[0] \
                if state_ok_servers and len(state_ok_servers) > 0 else None

        # catch any resource not found exception for
        # missing image, flavour or keypair, which used by the VM
        # exception message should be printed before exception was raised
        except exceptions.ResourceNotFoundException:
            migration_record.update({'migration_state':
                                         InstanceMigrationState.error})
            instances.update_migration_record(**migration_record)

        except Exception as e:
            LOG.error("Proxy VM[%s] creation error: %s" % (server.name, str(e)))
            traceback.print_exc()
            migration_record.update({'migration_state':
                                         InstanceMigrationState.error})
            instances.update_migration_record(**migration_record)

    def start_vms(self, nova_client, servers):

        """function to boots instances

        :param nova_client: the nova client that used to locate the instance
        :param servers: migration record of instances that needs to boot
        """
        LOG.info("Attempting to boot %d instance(s)" % len(servers))

        vms_to_poll = []
        for server in servers:
            try:
                vm = nova_client.servers.get(server['dst_uuid'])
            except nova_exceptions.NotFound:
                LOG.error("Server instance [Name: '{0}' ID: '{1}'] does not "
                          "exist on cloud '{2}'"
                          .format(server['dst_server_name'],
                                  server['dst_uuid'], server['dst_cloud']))

                server.update({'migration_state':
                                InstanceMigrationState.proxy_instance_missing})
                instances.update_migration_record(**server)
                continue

            # store source vm id, source cloud name destination cloud name in
            # this target vm object in order to update database records
            setattr(vm, 'src_uuid', server['src_uuid'])
            setattr(vm, 'src_cloud', server['src_cloud'])
            setattr(vm, 'dst_cloud', server['dst_cloud'])

            status = getattr(vm, 'status')
            if status == 'SHUTOFF':
                vm.start()
                vms_to_poll.append(vm)

        self.poll_vms_status(
            nova_client, vms_to_poll=vms_to_poll,
            ok_status=self.valid_states,
            ok_m_state=InstanceMigrationState.completed,
            break_m_state=InstanceMigrationState.instance_booting_failed,
            call_back=self.save_status,
            max_polls=12, verbose=True)  # 1 min

    def stop_vms(self, nova_client, servers):

        """function to shutoff instance

        :param nova_client: the nova client that used to locate the instance
        :param servers: migration record of instances that needs to stop
        """

        LOG.info("Attempting to shutting off %d instance(s)" % len(servers))

        vms_to_poll = []
        for server in servers:
            try:
                vm = nova_client.servers.get(server['dst_uuid'])
            except nova_exceptions.NotFound:
                LOG.error("Server instance [Name: '{0}' ID: '{1}'] does not "
                          "exist on cloud '{2}'"
                          .format(server['src_server_name'], server['src_uuid'],
                                  server['dst_cloud']))

                # updating database record
                server.update({'migration_state':
                                   InstanceMigrationState.stop_instance_failed})
                instances.update_migration_record(**server)
                continue

            # store source vm id, source cloud name destination cloud name in
            # this target vm object in order to update database records
            setattr(vm, 'src_uuid', server['src_uuid'])
            setattr(vm, 'src_cloud', server['src_cloud'])
            setattr(vm, 'dst_cloud', server['dst_cloud'])

            status = getattr(vm, 'status')
            if status == 'ACTIVE':
                vm.stop()
                vms_to_poll.append(vm)

        self.poll_vms_status(
            nova_client, vms_to_poll=vms_to_poll,
            ok_status=self.valid_states[3],
            ok_m_state=InstanceMigrationState.dst_instance_stopped,
            break_m_state=InstanceMigrationState.stop_instance_failed,
            call_back=self.save_status,
            max_polls=12, verbose=True)  # 1 min

    @staticmethod
    def copy_vm(s_server_id, t_server_id):

        dst_username = cfg.CONF.TARGET.os_host_username
        dst_password = base64.b64decode(cfg.CONF.TARGET.os_host_password)

        # preparing source files addresses
        base_loc = '/opt/stack/data/nova/instances'
        src_disk_loc = "%s/%s/disk" % (base_loc, s_server_id)

        src_host_user = cfg.CONF.SOURCE.os_host_username
        src_host_address = \
            str(cfg.CONF.SOURCE.os_auth_url).split("http://")[1].split(":")[0]
        from_loc = '%s@%s:%s' % (src_host_user, src_host_address, src_disk_loc)

        # preparing destination files addresses
        dst_disk_loc = "%s/%s/disk" % (base_loc, t_server_id)
        dst_host_address = \
            str(cfg.CONF.TARGET.os_auth_url).split("http://")[1].split(":")[0]

        # backup existing disk file at destination
        backup_command = ["mv", dst_disk_loc, dst_disk_loc + "_backup_%s" % \
                                              (datetime.now().strftime(
                                                  "%Y-%m-%d-%H-%M-%S"))]
        backup_command_str = ' '.join(backup_command)

        execute_remote_command(dst_host_address, dst_username,
                               dst_password, backup_command_str)

        # ssh command used to log into destination
        ssh_cmd = '\"ssh -i /home/' + dst_username + '/.ssh/id_rsa\"'

        # copy disk file from source to destination
        rsync_cmd = ["sudo", "/usr/bin/rsync", "-e", ssh_cmd,
                     '-avz', '--sparse', '--progress', from_loc, dst_disk_loc]
        rsync_cmd_str = ' '.join(rsync_cmd)

        [rsync_output, rsync_error] = execute_remote_command(
            dst_host_address, dst_username, dst_password, rsync_cmd_str)

        # if there are error
        if rsync_error:
            raise Exception("Error copying disk file from source to "
                            "destination\nDetails: %s" % rsync_error)

    def copy_vms(self, s_nova_client, t_nova_client, src_uuid, dst_uuid):
        """
            Copy an individual vm disk file across two hypervisors.
        """
        LOG.info("copying disk file between: \n"
                 "source instances [ID:%s] and\n"
                 "destination instances [ID:%s]" % (src_uuid, dst_uuid))

        # preparing database update
        data_update = {"src_uuid": src_uuid,
                       "src_cloud": self.s_cloud_name,
                       "dst_cloud": self.t_cloud_name}

        # double check the server instance hasn't got deleted
        # in the middle of migration
        try:
            source_server = s_nova_client.servers.get(src_uuid)
            # status = getattr(server, 'status').upper()
        except nova_exceptions.NotFound:
            LOG.error("Server instance [ID: {0}] doesn't exist in tenant {1}"
                      .format(src_uuid, s_nova_client.projectid))
            # update record
            data_update.update({'migration_state':
                                InstanceMigrationState.source_instance_missing})
            instances.update_migration_record(**data_update)
            return

        try:
            target_server = t_nova_client.servers.get(dst_uuid)
        except nova_exceptions.NotFound:
            LOG.error("Server instance [ID: {0}] doesn't exist in tenant {1}"
                      .format(dst_uuid, t_nova_client.projectid))
            # update record
            data_update.update({'migration_state':
                                InstanceMigrationState.proxy_instance_missing})
            instances.update_migration_record(**data_update)
            return

        # LOG.info("Shutting down source instance[%s]" % source_server.name)

        # try:
        #     source_server.stop()
        # except Exception as e:
        #     print "Fail to stop source server instance: %s" % str(e.message)
        #     # update record
        #     data_update.update({'migration_state': 'Stop_source_failed'})
        #     instances.update_migration_record(**data_update)
        #     return

        self.copy_vm(source_server.id, target_server.id)

        data_update.update({'migration_state':
                            InstanceMigrationState.disk_file_migrated})
        instances.update_migration_record(**data_update)

        #TODO: rebase when necessary

        LOG.info("done copying images")

        return target_server

    def migrate_vms(self, s_nova_client, t_nova_client, proxy_created_servers):

        LOG.info("Copying server instances for tenant '%s'....."
                 % s_nova_client.projectid)

        disk_copied_servers = []
        for server_record in proxy_created_servers:
            try:
                copied_server = self.copy_vms(s_nova_client, t_nova_client,
                                              server_record['src_uuid'],
                                              server_record['dst_uuid'])
                if copied_server:
                    disk_copied_servers.append(server_record)
            except Exception as e:
                LOG.error(e.message)
                server_record.update(
                    {'migration_state':
                         InstanceMigrationState.disk_file_migrate_failed})
                instances.update_migration_record(**server_record)

        return disk_copied_servers

    @staticmethod
    def load_instances(starting_states):
        instance_to_process = []
        servers = instances.get_migrated_vm()
        if servers:
            for server in servers:
                if server['migration_state'] in starting_states:
                    instance_to_process.append(server)

        return instance_to_process

    def execute(self, tenant_vm_dicts):

        """execute instance migration task

        :param tenant_vm_dicts: a dictionary which provides the tenant and
        particular instances of the tenant desired to migrate

        'tenant_vm_dicts' structure:
        ---- {tenant_name: list of vm ids,
        ----  tenant_name: list of vm ids,
        ----  ...}
        """

        if type(tenant_vm_dicts) is dict and len(tenant_vm_dicts) == 0:
            LOG.info("No VMs to be migrated.")
            return

        # collect servers from each given or existing tenant
        # vm_to_migrate is a <nova_client, vm_list> dictionary
        vm_to_migrate = {}
        source_nova_client = None

        if tenant_vm_dicts is not None:
            LOG.info("Migrating instances for tenants : [%s]"
                     % tenant_vm_dicts.keys())
            for tenant_name, vm_id_list in tenant_vm_dicts.iteritems():
                vm_list = []
                for vm_id in vm_id_list:
                    source_nova_client = get_nova_source(tenant_name)
                    try:
                        server = source_nova_client.servers.find(id=vm_id)
                    except nova_exceptions.NotFound:
                        raise exceptions.ResourceNotFoundException(
                            ResourceType.vm, vm_id, self.s_cloud_name)
                    vm_list.append(server)

                vm_to_migrate.update({source_nova_client: vm_list})
        else:
            LOG.info('Migrating instances for all tenants...')
            for tenant in self.ks_source.tenants.list():

                source_nova_client = get_nova_source(tenant.name)
                vm_list = []
                for server in source_nova_client.servers.list():
                    vm_list.append(server)

                vm_to_migrate.update({source_nova_client: vm_list})

        # migrate each server from each given or existing tenant
        for source_nova_client, vm_list in vm_to_migrate.iteritems():

            source_cloud = cfg.CONF.SOURCE.os_cloud_name
            target_cloud = cfg.CONF.TARGET.os_cloud_name
            tenant_name = source_nova_client.projectid
            values = [tenant_name, source_cloud, target_cloud]

            migrated_tenant = tenants.get_migrated_tenant(values)
            if not migrated_tenant:
                LOG.info("Skipping instances migration for tenant '%s' since "
                         "the tenant itself hasn't been migrated" % tenant_name)
                continue

            # check migrated tenant actually exist on target cloud
            dst_uuid = migrated_tenant['dst_uuid']
            try:
                dst_tenant = self.ks_target.tenants.find(id=dst_uuid)
            except keystone_exceptions.NotFound:
                LOG.error(
                    "Migrated tenant '{0}' required does not exist on "
                    "destination cloud {1}".format(tenant_name, target_cloud))
                # encapsulate exceptions to make it more understandable
                # to user. Other exception handling mechanism can be added later
                raise exceptions.ResourceNotFoundException(
                    ResourceType.tenant, tenant_name, self.t_cloud_name)

            target_nova_client = get_nova_target(dst_tenant.name)

            for vm in vm_list:
                self.create_proxy_vm(vm, source_nova_client,
                                     target_nova_client)

            # all VMs that has proxy created will potentially
            # be stopped and being migration. Loading details of them

            # There are several stages of migrating instances and the program
            # can fail at any stage. Loading migration record from database
            # can help with picking up from migration state left over in last
            #  run if there were any interruptions

            # states that are valid starting point of stopping instances
            stop_status = [InstanceMigrationState.proxy_launched,
                           InstanceMigrationState.stop_instance_failed]
            servers_to_stop = self.load_instances(stop_status)
            if servers_to_stop:
                self.stop_vms(target_nova_client, servers_to_stop)

            # only copy disk file for those instances of which the
            # corresponding destination instance that has been stopped
            # states that are valid starting point of stopping instances
            copy_states = [InstanceMigrationState.dst_instance_stopped,
                           InstanceMigrationState.disk_file_migrate_failed]
            servers_to_copy = self.load_instances(copy_states)
            if servers_to_copy:
                self.migrate_vms(source_nova_client, target_nova_client,
                                 servers_to_copy)

            # boot those instances that has disk file copied over
            boot_states = [InstanceMigrationState.disk_file_migrated,
                           InstanceMigrationState.instance_booting_failed]
            servers_to_boot = self.load_instances(boot_states)
            if servers_to_boot:
                self.start_vms(target_nova_client, servers_to_boot)