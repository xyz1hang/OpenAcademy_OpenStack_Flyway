from datetime import datetime
import os
import shutil
import subprocess

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
        migrated_flavors = flavors.get_migrated_flavor(filter_values)
        m_flavor = migrated_flavors[0] if migrated_flavors else None
        if not m_flavor:
            print("Flavor '{0}' required by instance [ID: {1}, Name: {2}] "
                  "hasn't been migrated yet."
                  .format(s_flavor.name, server.id, server.name))
            return None

        # try to get its corresponding flavor on destination cloud
        dst_flavor_id = m_flavor['dst_uuid']
        try:
            flavor_to_use = t_nova_client.flavors.find(id=dst_flavor_id)
        except nova_exceptions.NotFound:
            print ("Migrated flavor '{0}' does not exist on destination "
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
        filter_values = [s_image.name, s_image.id, self.s_cloud_name,
                         self.t_cloud_name]
        migrated_images = images.get_migrated_image(filter_values)
        m_image = migrated_images[0] if migrated_images else None
        if not m_image:
            print("Image '{0}' required by instance [ID: {1}, Name: {2}] "
                  "hasn't been migrated yet."
                  .format(s_image.name, server.id, server.name))
            return None

        # try to get its corresponding image on destination cloud
        gl_target = get_glance_client(self.ks_target)
        dst_image_id = m_image['dst_uuid']
        try:
            image_to_use = gl_target.image.get(dst_image_id)
        except glance_exceptions.HTTPNotFound:
            print ("Migrated image required by instance [ID: {1}, Name: {2}] "
                   "'{0}' does not exist on destination cloud '{1}'"
                   .format(s_image.name, self.t_cloud_name))
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
        m_keypair = migrated_keypairs[0] if migrated_keypairs else None
        if not m_keypair:
            print("keypair '{0}' required by instance [ID: {1}, Name: {2}] "
                  "hasn't been migrated yet."
                  .format(s_keypair.name, server.id, server.name))
            return None

        # try to get its corresponding keypair on destination cloud
        dst_keypair_name = m_keypair['new_name']
        try:
            keypair_to_use = t_nova_client.keypairs.find(name=dst_keypair_name)
        except nova_exceptions.NotFound:
            print ("Migrated keypair required by instance [ID: {1}, Name: {2}] "
                   "'{0}' does not exist on destination cloud '{1}'"
                   .format(s_keypair.name, self.t_cloud_name))
            raise exceptions.ResourceNotFoundException(
                ResourceType.vm, s_keypair_name, self.s_cloud_name)

        return keypair_to_use

    @staticmethod
    def save_status(result, vm, status):
        data_update = {}
        if result == 'success':
            print "Proxy VM[%s] created. Status: '%s'" % (vm.name, status)
            data_update = {'dst_uuid': vm.id,
                           'migration_state': 'proxy_created'}
        elif result == 'error':
            print "Proxy VM[%s] launching error. Status: '%s' " \
                  % (vm.name, status)
            data_update = {'dst_uuid': vm.id,
                           'migration_state': 'proxy_creation_failed'}

        instances.update_migration_record(**data_update)

    @staticmethod
    def poll_vms_status(nova_client, vms_to_poll,
                        ok_status, break_status='ERROR',
                        call_back=None, poll_interval=5, max_polls=5,
                        verbose=False):

        """function to check for states of s list of given server instance

        :param nova_client: nova python client that used to retrieve data
        about instance on the OpenStack deployment
        :param vms_to_poll: List of server instance objects to poll state for
        :param ok_status: List of user defined status regarded as OK
        :param break_status: List of user defined error status
        :param call_back: function to call upon state retrieved
        :param poll_interval: time between two consecutive polls
        :param max_polls: maximum number of poll attempt for each instance
        :param verbose: flag to indicate whether to be verbose during polling
        """
        num_of_poll = [0] * len(vms_to_poll)
        while len(vms_to_poll) > 0:

            for vm in vms_to_poll:
                # check for max number of polls
                index = vms_to_poll.index(vm)
                if num_of_poll[index] == max_polls:
                    print ("Maximum number of poll({0}) has been exceeded for "
                           "instance [Name: {1}, ID: {2}]".
                           format(max_polls, vm.name, vm.id))
                    call_back(result="ERROR", vm=vm, status="unknown")
                    vms_to_poll.remove(vm)
                    del num_of_poll[index]
                    continue

                if verbose:
                    print ("polling status of instance [Name: {0}, ID: {1}].."
                           "....".format(vm.name, vm.name))
                try:
                    server = nova_client.servers.get(vm.id)
                    status = getattr(server, 'status').upper()
                except nova_exceptions.NotFound:
                    print ("Server instance [Name: {0}, ID: {1}] doesn't "
                           "exist in tenant {2}".format(vm.name, vm.id,
                                                        nova_client.projectid))
                    status = break_status

                result = "success" if status in ok_status else "error" \
                    if status in break_status else None
                if result:
                    vms_to_poll.remove(vm)
                    del num_of_poll[index]
                    if call_back:
                        try:
                            call_back(result=result, vm=vm, status=status)
                        except Exception:
                            traceback.print_exc()
                            pass

                num_of_poll[index] += 1
                time.sleep(poll_interval)

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

        #TODO: 1. implement -nics
        #TODO: 2. How do we update other meta data e.g. security group
        #TODO:    does it has to be the same as that the VM used on source
        #TODO:    cloud ?

        proxy_vm = t_nova_client.servers.create(name=server.name,
                                                image=image_to_use,
                                                flavor=flavor_to_use,
                                                keypairs=keypair_to_use)
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

        src_tenant = s_nova_client.projectid
        dst_tenant = t_nova_client.projectid
        # preparing for database record
        instance_migration_data = {
            'src_server_name': server.name,
            'src_uuid': server.id,
            'src_cloud': self.s_cloud_name,
            'src_tenant': src_tenant,
            'dst_server_name': server.name,
            'dst_cloud': self.t_cloud_name,
            'dst_uuid': 'NULL',
            'dst_tenant': dst_tenant,
            'migration_state': 'launching_proxy'}

        data_update = {}

        instances.record_vm_migrated(**instance_migration_data)

        instance_state = getattr(server, 'status')
        if not ignore_vm_state and instance_state not in self.valid_states:
            message = "Skipping VM[%s] due to state '%s'" % \
                      (server.name, getattr(server, 'status'))
            print message
            data_update.update({'migration_state': 'skipped'})
            instances.update_migration_record(**data_update)
            return None

        # check whether the vm has been migrated
        filters = {"src_server_name": server.name,
                   "src_uuid": server.id,
                   "src_tenant": src_tenant,
                   "src_cloud": self.s_cloud_name,
                   "dst_cloud": self.t_cloud_name}

        migrated_instances = instances.get_migrated_vm(**filters)

        instance = migrated_instances[0] if migrated_instances else None

        if len(migrated_instances) > 1:
            print("Error - Multiple migration records found for "
                  "instance '{0}' from tenant '{1}' in cloud '{2}'"
                  .format(filters['src_server_name'], filters['src_tenant'],
                          filters['src_cloud']))
            return None

        if instance:
            # check whether destination id is not or not
            # i.e whether the proxy exists on destination or not
            dst_uuid = getattr(instance, 'dst_uuid', None)
            if dst_uuid:
                migration_state = getattr(instance, 'migration_state', None)
                if migration_state == "completed":
                    print "VM[ID: %s, Name: %s] has been migrated" % \
                          (instance.src_uuid, instance.src_server_name)
                    return
                if migration_state == "proxy_created":
                    print "Proxy instance for VM[ID: %s, Name: %s] has been " \
                          "created" % (instance.src_uuid,
                                       instance.src_server_name)
                    return

        print "creating proxy instance in destination cloud for " \
              "instance '%s' with source id '%s'" \
              % (server.name, server.id)

        try:
            p_server = self.create_vm(server, s_nova_client, t_nova_client)
            if not p_server:
                return

            # check for VM spawning status
            self.poll_vms_status(nova_client=t_nova_client,
                                 vms_to_poll=[p_server],
                                 ok_status=self.valid_states,
                                 call_back=self.save_status)

        except exceptions.ResourceNotFoundException:
            data_update.update({'migration_state': 'error'})

        except Exception as e:
            print "Proxy VM[%s] creation error: %s" % \
                  (server.name, str(e))
            data_update.update({'migration_state': 'error'})
            traceback.print_exc()
        finally:
            instances.update_migration_record(**data_update)

    def start_vms(self, nova_client, servers):

        LOG.info("Total %d potential vms to start" % len(servers))

        vms_to_poll = []
        for server in servers:
            try:
                vm = nova_client.servers.get(server['dst_uuid'])
            except nova_exceptions.NotFound:
                print "Server instance [Name: '{0}' ID: '{1}'] does not " \
                      "exist on cloud '{2}'".format(server['src_server_name'],
                                                    server['src_uuid'],
                                                    server['dst_cloud'])
                data_update = server
                data_update.update({'migration_state': 'completed'})
                instances.update_migration_record(**data_update)
                continue

            status = getattr(vm, 'status')
            if status == 'SHUTOFF':
                vm.start()
                vms_to_poll.append(vm)

        self.poll_vms_status(nova_client, vms_to_poll=vms_to_poll,
                             ok_status=self.valid_states,
                             max_polls=12, verbose=True)  # 1 min

    def stop_vms(self, nova_client, proxy_created_servers):

        LOG.info("Found %d potential vms to stop" % len(proxy_created_servers))

        vms_to_poll = []
        for server in proxy_created_servers:
            try:
                vm = nova_client.servers.get(server['dst_uuid'])
            except nova_exceptions.NotFound:
                print "Server instance [Name: '{0}' ID: '{1}'] does not " \
                      "exist on cloud '{2}'".format(server['src_server_name'],
                                                    server['src_uuid'],
                                                    server['dst_cloud'])
                # preparing database update
                data_update = server
                data_update.update({'migration_state': 'proxy_creation_failed'})
                instances.update_migration_record(**data_update)
                continue

            status = getattr(vm, 'status')
            if status == 'ACTIVE':
                vm.stop()
                vms_to_poll.append(vm)

        self.poll_vms_status(nova_client, vms_to_poll=vms_to_poll,
                             ok_status=self.valid_states,
                             max_polls=12, verbose=True)  # 1 min

    @staticmethod
    def copy_vm(s_server_id, t_server_id, ssh_cmd="ssh"):

        base_loc = '/opt/stack/data/nova/instances/'
        src_disk_loc = "%s/%s/disk" % (base_loc, s_server_id)

        # check for kernel or ramdisk in case they exists
        # kernel_disk_loc = "%s/%s/kernel" % (base_loc, s_server_id)
        # ramdisk_disk_loc = "%s/%s/ramdisk" % (base_loc, s_server_id)

        src_host_user = cfg.CONF.SOURCE.os_host_username
        src_host_address = \
            str(cfg.CONF.SOURCE.os_auth_url).split("http://")[1].split(":")

        from_loc = '%s@%s:%s' % (src_host_user, src_host_address, src_disk_loc)
        dst_disk_loc = "%s/%s/disk" % (base_loc, t_server_id)

        # backup existing disk file at destination
        if os.path.exists(dst_disk_loc):
            backup_file = dst_disk_loc + "_backup_%s" % \
                          (datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))

            shutil.move(dst_disk_loc, backup_file)

        # preparing rsync command to execute
        cmd = ["/usr/bin/rsync", "-e", ssh_cmd,
               '-avz', '--sparse', '--progress', from_loc, dst_disk_loc]
        print "Executing " + ' '.join(cmd)

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        message = None
        while process.poll() is None:
            message = process.communicate()
            print message

        if not process.returncode == 0:
            raise Exception("rsync ended up with status code %d and "
                            "last message was %s"
                            % (process.returncode, message))

    def copy_vms(self, s_nova_client, t_nova_client, src_uuid, dst_uuid):
        """
            Copy an individual vm disk file across two hypervisors.
        """
        print "copying disk file between\n" \
              "source instances [ID:%s] and\n " \
              "destination instances [ID:%s]" % (src_uuid, dst_uuid)

        # preparing database update
        data_update = {"src_uuid": src_uuid,
                       "src_cloud": self.s_cloud_name,
                       "dst_cloud": self.t_cloud_name}

        # double check the server instance hasn't got deleted
        # in the middle of migration
        source_server = None
        target_server = None
        try:
            source_server = s_nova_client.servers.get(src_uuid)
            # status = getattr(server, 'status').upper()
        except nova_exceptions.NotFound:
            print ("Server instance [Name: {0}, ID: {1}] doesn't "
                   "exist in tenant {2}".format(source_server.name,
                                                source_server.id,
                                                s_nova_client.projectid))
            # update record
            data_update.update({'migration_state': 'source_not_exist'})
            instances.update_migration_record(**data_update)
            return

        try:
            target_server = t_nova_client.servers.get(dst_uuid)
        except nova_exceptions.NotFound:
            print ("Server instance [Name: {0}, ID: {1}] doesn't "
                   "exist in tenant {2}".format(target_server.name,
                                                target_server.id,
                                                t_nova_client.projectid))
            # update record
            data_update.update({'migration_state': 'proxy_not_exist'})
            instances.update_migration_record(**data_update)
            return

        print "shutting down source server instance[%s] to shutdown" % \
              source_server.name

        try:
            source_server.stop()
        except Exception as e:
            print "Fail to stop source server instance: %s" % str(e.message)
            # update record
            data_update.update({'migration_state': 'proxy_not_exist'})
            instances.update_migration_record(**data_update)
            return

        #TODO: generate key
        self.copy_vm(source_server.id, target_server.id,
                     ssh_cmd='ssh -l vagrant '
                             '-o UserKnownHostsFile=/dev/null '
                             '-o StrictHostKeyChecking=no')

        data_update = {'migration_state': 'disk file copied'}
        instances.update_migration_record(**data_update)

        #TODO: rebase only if necessary , raw images may not need it
        # data = rebase(dst_server)

        # data_update = {'migration_state': 'rebased'}
        # instances.update_migration_record(**data_update)

        print "done copying images and rebasing"

        return target_server

    def migrate_vms(self, s_nova_client, t_nova_client, proxy_created_servers):
        print "Copying server instances for tenant '%s'....." \
              % s_nova_client.projectid

        disk_copied_servers = []
        for server in proxy_created_servers:
            copied_server = self.copy_vms(s_nova_client, t_nova_client,
                                          server['src_uuid'],
                                          server['dst_uuid'])
            if copied_server:
                disk_copied_servers.append(copied_server)

        return disk_copied_servers

    def execute(self, tenant_vm_dicts=None):

        """execute instance migration task

        :param tenant_vm_dicts: a dictionary which provides the tenant and
        particular instances of the tenant desired to migrate

        'tenant_vm_dicts' list structure:
        ---- {tenant_name: list of vm ids}
        ---- {tenant_name: list of vm ids}
        ---- ...
        """

        # collect servers from each given or existing tenant
        # vm_to_migrate is a <nova_client, vm_list> dictionary
        vm_to_migrate = {}
        source_nova_client = None

        if tenant_vm_dicts:
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

                if tenant.name == "invisible_to_admin":
                    continue

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
                print ("Skipping instances migration for tenant '%s' since "
                       "the tenant itself hasn't been migrated" % tenant_name)
                continue

            # check migrated tenant actually exist on target cloud
            dst_uuid = migrated_tenant['dst_uuid']
            try:
                dst_tenant = self.ks_target.tenants.find(id=dst_uuid)
            except keystone_exceptions.NotFound:
                print ("Migrated tenant '{0}' required by instance [ID: {1}, "
                       "Name: {2}]  does not exist on destination "
                       "cloud {1}".format(tenant_name, target_cloud))
                # encapsulate exceptions to make it more understandable
                # to user. Other exception handling mechanism can be added later
                raise exceptions.ResourceNotFoundException(
                    ResourceType.tenant, tenant_name, self.t_cloud_name)

            target_nova_client = get_nova_target(dst_tenant.name)
            for vm in vm_list:
                self.create_proxy_vm(vm, source_nova_client, target_nova_client)

            # all VMs that as proxy created will potentially
            # be stopped and being migration
            data_filter = {"migration_state": "proxy_created"}
            proxy_created_servers = instances.get_migrated_vm(**data_filter)

            self.stop_vms(target_nova_client, proxy_created_servers)
            migrated_servers = self.migrate_vms(source_nova_client,
                                                target_nova_client,
                                                proxy_created_servers)
            self.start_vms(target_nova_client, migrated_servers)