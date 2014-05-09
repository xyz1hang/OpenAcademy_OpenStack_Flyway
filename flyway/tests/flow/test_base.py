from testtools import TestCase
from utils.db_handlers import environment_config
from common import config


__author__ = 'hydezhang'


class TestBase(TestCase):
    """base class of tests. Please put all common logic here (setup etc.)

    """

    def __init__(self, *args, **kwargs):
        super(TestBase, self).__init__(*args, **kwargs)
        config.parse(['--config-file', '../../etc/flyway.conf'])
        environment_config.initialize_environment()