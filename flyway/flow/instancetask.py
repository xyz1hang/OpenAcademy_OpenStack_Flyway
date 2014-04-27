import logging
import traceback

from taskflow import task
from novaclient import exceptions as nova_exceptions
from keystoneclient import exceptions as keystone_exceptions
from glanceclient import exc as glance_exceptions
import time

from utils import exceptions
from utils.db_handlers import instances, tenants, flavors, images, keypairs
from utils.helper import *
from utils.resourcetype import ResourceType


LOG = logging.getLogger(__name__)


class InstanceMigrationTask(task.Task):
    """
    Task to migrate all instances from the source cloud to the target cloud.
    """

    def __init__(self, **kwargs):
        super(InstanceMigrationTask, self).__init__(**kwargs)
        self.ks_source = get_keystone_source()
        self.ks_target = get_keystone_target()

        self.s_cloud_name = cfg.CONF.SOURCE.os_cloud_name
        self.t_cloud_name = cfg.CONF.TARGET.os_cloud_name

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
    def poll_vms_status(nova_client, vms_to_poll, ok_status,
                        break_status='ERROR', call_back=None,
                        poll_interval=5, max_polls=0, verbose=False):

        num_of_poll = [0] * len(vms_to_poll)
        while len(vms_to_poll) > 0:

            for vm in vms_to_poll:
                # check for max number of polls
                index = vms_to_poll.index(vm)
                if num_of_poll[index] == max_polls:
                    print ("Maximum number of poll{0} has been exceeded for "
                           "instance [Name: {1}, ID: {2}]".
                           format(max_polls, vm.name, vm.id))
                    call_back(result="ERROR", vm=vm, status="unknown")
                    vms_to_poll.remove(vm)
                    del num_of_poll[index]
                    continue

                if verbose:
                    print ("polling status of instance [Name: {0}, ID: {1}].."
                           "....".format(vm.name, vm.name))

                server = nova_client.servers.get(vm.id)
                status = getattr(server, 'status').upper()
                result = "success" if status in ok_status else "error" if \
                    status in break_status else None
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
        #TODO: 3. How do we update other meta data e.g. security group
        #TODO:    does it has to be the same as that the VM used on source
        #TODO:    cloud ?

        proxy_vm = t_nova_client.servers.create(server=server.name,
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
        valid_states = ['ACTIVE', 'PAUSED', 'SUSPENDED', 'SHUTOFF']
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
        if not ignore_vm_state and instance_state not in valid_states:
            message = "Skipping VM[%s] due to state '%s'" % \
                      (server.name, getattr(server, 'status'))
            print message
            data_update.update({'migration_state': 'error'})
            instances.update_migration_record(**data_update)
            return None

        # check whether the vm has been migrated
        values = [server.name, server.id, src_tenant,
                  self.s_cloud_name, self.t_cloud_name]
        migrated_instances = instances.get_migrated_vm(values)

        instance = migrated_instances[0] if migrated_instances else None
        if instance:
            if instance.dst_uuid and instance['migration_state'] == "completed":
                print "VM[ID: %s, Name: %s] has been migrated" % \
                      (instance.src_uuid, instance.src_server_name)
                return
            if instance.dst_uuid and \
                            instance.migration_state != "launched_proxy":
                return

        print "creating proxy instance in destination cloud for " \
              "instance '%s' with source id '%s'" \
              % (server.name, server.id)

        try:
            p_server = self.create_vm(server, s_nova_client, t_nova_client)
            if not p_server:
                return

            self.poll_vms_status(nova_client=t_nova_client,
                                 vms_to_poll=[p_server],
                                 ok_status=valid_states,
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

    def execute(self, tenant_vm_dicts=None):

        """execute instance migration task

        :param tenant_vm_dicts: a dictionary which provides the tenant and
        particular instances of the tenant desired to migrate

        'tenant_vm_dicts' list structure:
        ---- {tenant_name: list of vm ids}
        ---- {tenant_name: list of vm ids}
        ---- ...
        """
        vm_to_migrate = {}
        # collect servers from each given or existing tenant
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

                vm_to_migrate.update({tenant_name: vm_list})
        else:
            LOG.info('Migrating instances for all tenants...')
            for tenant in self.ks_source.tenants.list():
                source_nova_client = get_nova_source(tenant.name)
                vm_list = []
                for server in source_nova_client.servers.list():
                    vm_list.append(server)

                vm_to_migrate.update({tenant.name: vm_list})

        # migrate each server from each given or existing tenant
        for tenant_name, vm_list in vm_to_migrate.iteritems():

            source_cloud = cfg.CONF.SOURCE.os_cloud_name
            target_cloud = cfg.CONF.TARGET.os_cloud_name
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
