from task_scheduler.default_image_scheduler import DefaultImageScheduler
from tests.flow.test_base import TestBase

__author__ = 'Sherlock'


class DefaultImageSchedulerTest(TestBase):
    def __init__(self, *args, **kwargs):
        super(DefaultImageSchedulerTest, self).__init__(*args, **kwargs)
        self.scheduler = DefaultImageScheduler()

    def test_sort(self):
        source_images = self.scheduler.gl_source.images.list()
        images = [{'img': img} for img in source_images]
        print self.scheduler.sort(images)