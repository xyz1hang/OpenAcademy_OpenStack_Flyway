from utils.helper import get_nova_source, get_glance_source

__author__ = 'Sherlock'


class DefaultImageScheduler(object):
    def __init__(self):
        self.nv_source = get_nova_source()
        self.gl_source = get_glance_source()

    def sort(self, images):

        image_ids = [image['img'].id for image in images]
        vms = self.nv_source.servers.list()
        image_ids_with_vms = [vm.image['id'] for vm in vms
                              if vm.image['id'] in image_ids]
        for image in images:
            if image.get('times', None) is None:
                image['times'] = \
                    image_ids_with_vms.count(image['img'].id)
        sorted_images = sorted(images,
                               key=lambda p: p['times'],
                               reverse=True)
        for sorted_image in sorted_images:
            sorted_image.pop('times', None)

        return sorted_images