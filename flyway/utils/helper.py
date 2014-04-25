import base64
import keystoneclient.v2_0.client as ksclient
import glanceclient.v1.client as glclient
import novaclient.v3.client as nvclient
import logging
import random
import smtplib

from common import config as cfg

LOG = logging.getLogger(__name__)


def get_keystone_source(tenant_name=None):
    """Get source keystone client
    :param tenant_name: the tenant that this keystone client corresponds to
    The default is the admin tenant
    """
    ks_source_credentials = get_credentials(cfg.CONF.SOURCE)
    if tenant_name:
        ks_source_credentials['tenant_name'] = tenant_name

    ks_client_source = get_keystone_client(**ks_source_credentials)
    return ks_client_source


def get_keystone_target(tenant_name=None):
    """Get target keystone client
    :param tenant_name: the tenant that this keystone client corresponds to
    The default is the admin tenant
    """
    ks_target_credentials = get_credentials(cfg.CONF.TARGET)
    if tenant_name:
        ks_target_credentials['tenant_name'] = tenant_name

    ks_client_target = get_keystone_client(**ks_target_credentials)
    return ks_client_target


def get_glance_source(source_keystone=None):
    """Get source glance client
    """
    ks_client = source_keystone
    if not source_keystone:
        ks_client = get_keystone_source()

    glance_source = get_glance_client(ks_client)
    return glance_source


def get_glance_target(target_keystone=None):
    """Get target glance client
    """
    ks_client = target_keystone
    if not target_keystone:
        ks_client = get_keystone_target()

    glance_source = get_glance_client(ks_client)
    return glance_source


def get_nova_source(tenant_name=None):
    """Get source nova client
    :param tenant_name: the tenant that this nova client corresponds to
    The default is the admin tenant
    """
    nv_source_credentials = get_credentials(cfg.CONF.SOURCE)
    if tenant_name:
        nv_source_credentials['tenant_name'] = tenant_name

    return get_nova_client(**nv_source_credentials)


def get_nova_target(tenant_name=None):
    """Get target nova client
    :param tenant_name: the tenant that this nova client corresponds to
    The default is the admin tenant
    """
    nv_target_credentials = get_credentials(cfg.CONF.TARGET)
    if tenant_name:
        nv_target_credentials['tenant_name'] = tenant_name

    return get_nova_client(**nv_target_credentials)


def get_endpoint(keystone_client, service_type, endpoint_type):
    """function to get endpoint url of OpenStack services

    :param keystone_client:
    :param service_type:
    :param endpoint_type:
    :return: endpoint url
    """
    return keystone_client.service_catalog.url_for(
        service_type=service_type, endpoint_type=endpoint_type)


def get_keystone_client(username=None, password=None,
                        auth_url=None, tenant_name=None):
    """Get keystone client
    """
    return ksclient.Client(username=username, password=password,
                           auth_url=auth_url, tenant_name=tenant_name)


def get_glance_client(keystone_client):
    """Get glance service from a given keystone
    :param keystone_client: the keystone client which exists on the same
    cloud as the glance client
    """
    glance_endpoint = get_endpoint(keystone_client, 'image', 'adminURL')
    glance = glclient.Client(endpoint=glance_endpoint,
                             token=keystone_client.auth_token)
    return glance


def get_nova_client(username=None, password=None,
                    auth_url=None, tenant_name=None):
    """Get nova client

    project_id is actually not needed.
    See nova client source code comments for more info
    """
    nova = nvclient.Client(username=username, password=password,
                           project_id=tenant_name, auth_url=auth_url)
    return nova


def get_credentials(credentials):
    """Get cloud keystone credentials
    :rtype dict
    """
    password = credentials.os_password
    password = base64.b64decode(password)

    credentials = {'username': credentials.os_username,
                   'password': password,
                   'auth_url': credentials.os_auth_url,
                   'tenant_name': credentials.os_tenant_name}
    return credentials


def generate_new_password(email=None, default_password='123456'):
    """
    Generate a random password for the user and email to the user,
    default_password is used if the user has no email
    """
    if email is not None:
        password = new_password()
        try:
            send_reset_password_email(email, password)
        except Exception, e:
            password = default_password
            LOG.error("Error happened when \
                       sending password-resetting email")
            LOG.error(e.message)

    else:
        password = default_password

    return password


def new_password():
    """Generate a new password containing 10 letters
    """
    letters = 'abcdegfhijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
    password = ''
    for i in range(10):
        random_number = int(random.random() * len(letters))
        password += letters[random_number]
    return password


def send_email(from_addr, to_addr_list, cc_addr_list, subject,
               message, login, password, smtpserver=cfg.CONF.EMAIL.smtpserver):
    """Send email using gmail
    """
    header = 'From: %s\n' % from_addr
    header += 'To: %s\n' % ','.join(to_addr_list)
    header += 'Cc: %s\n' % ','.join(cc_addr_list)
    header += 'Subject: %s\n\n' % subject
    message = header + message

    server = smtplib.SMTP(smtpserver)
    server.starttls()
    server.login(login, password)
    server.sendmail(from_addr, to_addr_list, message)
    server.quit()


def send_reset_password_email(email_addr, password):
    msg_content = "Your password has been reset to " + password \
                  + " because of resource migration." \
                  + "\nPlease change your password. Thank you."
    email = {'from_addr': "openstack.flyway@gmail.com",
             'to_addr_list': [email_addr],
             'cc_addr_list': [],
             'subject': "Flyway: Please change your password",
             'message': msg_content,
             'login': cfg.CONF.EMAIL.login,
             'password': cfg.CONF.EMAIL.password
             }
    send_email(**email)
