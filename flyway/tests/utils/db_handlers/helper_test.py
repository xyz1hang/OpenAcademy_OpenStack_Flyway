from tests.utils.db_handlers.test_base import TestBase

__author__ = 'chengxue'

from utils.helper import *
from oslo.config import cfg as cfg_test


class HelperDBHandlerTest(TestBase):

    def __init__(self, *args, **kwargs):
        super(HelperDBHandlerTest, self).__init__(*args, **kwargs)

        self.s_host = cfg.CONF.SOURCE. \
            os_auth_url.split("http://")[1].split(":")[0]

    def test_get_credentials(self):
        group = cfg_test.OptGroup(name='TEST', title='Testing')

        data = [
            cfg_test.StrOpt('os_auth_url', default='url'),
            cfg_test.StrOpt('os_tenant_name', default='tenant_name'),
            cfg_test.StrOpt('os_username', default='user_name'),
            cfg_test.StrOpt('os_password', default='')
        ]

        CONF = cfg_test.CONF
        CONF.register_group(group)
        CONF.register_opts(data, group)
        the_credentials = get_credentials(cfg_test.CONF.TEST)

        credentials = {'username': 'user_name',
                       'password': '',
                       'auth_url': 'url',
                       'tenant_name': 'tenant_name'}

        self.assertDictEqual(the_credentials, credentials)

    def test_functions_get_source_target(self):
        source = get_keystone_source()
        self.assertIsNotNone(source)

        target = get_keystone_target()
        self.assertIsNotNone(target)

        source = get_glance_source()
        self.assertIsNotNone(source)

        target = get_glance_target()
        self.assertIsNotNone(target)

        source = get_nova_source()
        self.assertIsNotNone(source)

        target = get_nova_target()
        self.assertIsNotNone(target)

    def test_generate_new_password(self):
        new_pass = generate_new_password()
        self.assertEqual("123456", new_pass)

        new_pass2 = generate_new_password(email="x@gmail.com")
        self.assertIsNot("123456", new_pass2)