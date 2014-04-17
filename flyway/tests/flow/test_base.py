from testtools import TestCase
from utils.db_handlers import environment_config

__author__ = 'hydezhang'


class TestBase(TestCase):
    """base class of tests. Please put all common logic here (setup etc.)

    """

    def __init__(self, *args, **kwargs):
        super(TestBase, self).__init__(*args, **kwargs)

    def setUp(self):
        super(TestBase, self).setUp()
        environment_config.initialize_environment()