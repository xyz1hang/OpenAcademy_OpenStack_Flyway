
from task_scheduler.default_image_scheduler import DefaultImageScheduler
from task_scheduler.default_vm_scheduler import DefaultVMScheduler

__author__ = 'Sherlock'
from oslo.config import cfg
image_scheduler = None
vm_scheduler = None


def setup_scheduler():
    global image_scheduler
    global vm_scheduler
    try:
        full_name = cfg.CONF.SCHEDULER.image_scheduler
        package_name, class_name = full_name.rsplit('.', 1)
        exec("from {0} import {1}".format(package_name, class_name))
        exec("image_scheduler = {0}()".format(class_name))
    except Exception, e:
        print "error"
        print e
        image_scheduler = DefaultImageScheduler()

    try:
        full_name = cfg.CONF.scheduler.image_scheduler
        package_name, class_name = full_name.rsplit('.', 1)
        exec("from {0} import {1}".format(package_name, class_name))
        exec("vm_scheduler = {0}()".format(cfg.CONF.scheduler.image_scheduler))
    except Exception:
        vm_scheduler = DefaultVMScheduler()





